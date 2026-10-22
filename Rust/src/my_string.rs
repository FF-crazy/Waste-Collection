use std::{
  ops::{Add, AddAssign, Deref},
};

#[derive(Debug, Clone)]
pub struct MyString {
  bytes: Vec<u8>,
  offsets: Vec<usize>,
}

impl MyString {
  pub fn new() -> MyString {
    MyString {
      bytes: Vec::new(),
      offsets: Vec::new(),
    }
  }

  fn check_char_valid(char: &[u8]) -> bool {
    match char.len() {
      1 => (char[0] & 0b1000_0000) == 0,
      2 => (char[0] & 0b1110_0000) == 0b1100_0000 && (char[1] & 0b1100_0000) == 0b1000_0000,
      3 => {
        (char[0] & 0b1111_0000) == 0b1110_0000
          && (char[1] & 0b1100_0000) == 0b1000_0000
          && (char[2] & 0b1100_0000) == 0b1000_0000
      }
      4 => {
        (char[0] & 0b1111_1000) == 0b1111_0000
          && (char[1] & 0b1100_0000) == 0b1000_0000
          && (char[2] & 0b1100_0000) == 0b1000_0000
          && (char[3] & 0b1100_0000) == 0b1000_0000
      }
      _ => false,
    }
  }

  fn split(chars: &[u8]) -> Result<Vec<Vec<u8>>, ()> {
    let mut res = Vec::new();
    let mut c = Vec::with_capacity(4);
    let mut i = 0;
    while i < chars.len() {
      c.clear();
      let x = chars[i];
      match x {
        0..=0x7F => {
          c.push(x);
          res.push(c.clone());
          c.clear();
          i += 1;
        }
        0xC0..=0xDF => {
          if i + 1 >= chars.len() || chars[i + 1] & 0b1100_0000 != 0b1000_0000 {
            return Err(());
          }
          c.push(x);
          c.push(chars[i + 1]);
          res.push(c.clone());
          i += 2;
        }
        0xE0..=0xEF => {
          if i + 2 >= chars.len()
            || chars[i + 1] & 0b1100_0000 != 0b1000_0000
            || chars[i + 2] & 0b1100_0000 != 0b1000_0000
          {
            return Err(());
          }
          c.push(x);
          c.push(chars[i + 1]);
          c.push(chars[i + 2]);
          res.push(c.clone());
          i += 3;
        }
        0xF0..=0xF7 => {
          if i + 3 >= chars.len()
            || chars[i + 1] & 0b1100_0000 != 0b1000_0000
            || chars[i + 2] & 0b1100_0000 != 0b1000_0000
            || chars[i + 3] & 0b1100_0000 != 0b1000_0000
          {
            return Err(());
          }
          c.push(x);
          c.push(chars[i + 1]);
          c.push(chars[i + 2]);
          c.push(chars[i + 3]);
          res.push(c.clone());
          i += 4;
        }
        _ => {
          return Err(());
        }
      }
    }
    Ok(res)
  }

  fn push(&mut self, char: &[u8]) {
    let pos = self.bytes.len();
    self.bytes.extend(char);
    self.offsets.push(pos);
  }
  fn convert_char(ch: char) -> Vec<u8> {
    let mut res = Vec::with_capacity(4);
    let c = ch as u32;
    match c {
      0..=0x007F => {
        res.push(c as u8);
      }
      0x0080..=0x07FF => {
        res.push((0b11000000 | c >> 6) as u8);
        res.push((0x80 | (c >> 0 & 0x3F)) as u8);
      }
      0x0800..=0xFFFF => {
        res.push((0b11100000 | c >> 12) as u8);
        res.push((0x80 | (c >> 6 & 0x3F)) as u8);
        res.push((0x80 | (c >> 0 & 0x3F)) as u8);
      }
      0x10000..=0x10FFFF => {
        res.push((0b11110000 | c >> 18) as u8);
        res.push((0x80 | (c >> 12 & 0x3F)) as u8);
        res.push((0x80 | (c >> 6 & 0x3F)) as u8);
        res.push((0x80 | (c >> 0 & 0x3F)) as u8);
      }
      _ => {}
    }
    res
  }
  pub fn push_char(&mut self, ch: char) {
    self.push(&MyString::convert_char(ch));
  }
  pub fn push_str(&mut self, s: &str) {
    let chars = s.as_bytes();
    let v = MyString::split(chars).expect("Never get a err");
    v.into_iter().for_each(|c| {
      self.offsets.push(self.bytes.len());
      self.bytes.extend(c);
    });
  }
  pub fn insert_char(&mut self, idx: usize, ch: char) -> Result<(), ()> {
    if idx > self.offsets.len() {
      return Err(());
    }
    let c = MyString::convert_char(ch);
    if idx == self.offsets.len() {
      self.push(&c);
      return Ok(());
    }
    let pos = self.offsets[idx];
    c.iter().enumerate().for_each(|(i, &x)| {
      self.bytes.insert(pos + i, x);
    });
    let n = c.len();
    let &last = self.offsets.last().expect("");
    for i in (idx + 1..self.offsets.len()).rev() {
      self.offsets[i] = n + self.offsets[i - 1];
    }
    self.offsets.push(last + n);
    Ok(())
  }
  pub fn insert_str(&mut self, idx: usize, s: &str) -> Result<(), ()> {
    if idx > self.offsets.len() {
      return Err(());
    }
    if idx == self.offsets.len() {
      self.push_str(s);
      return Ok(());
    }
    let chars = MyString::split(s.as_bytes()).expect("Never get a err");
    let pos = self.offsets[idx];
    let k = chars.len();
    let str_bytes = chars.iter().fold(0, |acc, v| acc + v.len());

    self.bytes.resize(self.bytes.len() + str_bytes, 0);
    self.offsets.resize(self.offsets.len() + k, 0);

    for i in (pos + str_bytes..self.bytes.len()).rev() {
      self.bytes[i] = self.bytes[i - str_bytes];
    }
    for i in (idx + k..self.offsets.len()).rev() {
      self.offsets[i] = self.offsets[i - k] + str_bytes;
    }
    let mut j = 0;
    chars.into_iter().enumerate().for_each(|(i, ch)| {
      self.offsets[idx + i] = pos + j;
      ch.into_iter().for_each(|x| {
        self.bytes[pos + j] = x;
        j += 1;
      });
    });

    Ok(())
  }
  pub fn get(&self, idx: usize) -> Option<char> {
    if idx >= self.offsets.len() {
      return None;
    }
    let begin = self.offsets[idx];
    let &end = self.offsets.get(idx + 1).unwrap_or(&self.bytes.len());
    let b = &self.bytes[begin..end];
    let ch = match b.len() {
      1 => b[0] as u32,
      2 => (b[0] as u32 & 0x1F) << 6 | (b[1] as u32 & 0x3F),
      3 => (b[0] as u32 & 0x0F) << 12 | (b[1] as u32 & 0x3F) << 6 | (b[2] as u32 & 0x3F),
      4 => {
        (b[0] as u32 & 0x07) << 18
          | (b[1] as u32 & 0x3F) << 12
          | (b[2] as u32 & 0x3F) << 6
          | (b[3] as u32 & 0x3F)
      }
      _ => return None,
    };
    char::from_u32(ch)
  }
  pub fn as_str(&self) -> &str {
    self.as_ref()
  }
  pub fn from(s: &str) -> Self {
    let mut res = Self::new();
    res.push_str(s);
    res
  }
}

impl Add<&str> for MyString {
  type Output = Self;
  fn add(self, rhs: &str) -> Self::Output {
    let mut output = self;
    output.push_str(rhs);
    output
  }
}
impl AddAssign<&str> for MyString {
  fn add_assign(&mut self, rhs: &str) {
    self.push_str(rhs);
  }
}
impl AsRef<str> for MyString {
  fn as_ref(&self) -> &str {
    unsafe { str::from_utf8_unchecked(&self.bytes) }
  }
}

// impl ToString for MyString {
//   fn to_string(&self) -> String {
//     unsafe { String::from_utf8_unchecked(self.bytes.clone()) }
//   }
// }
impl Deref for MyString {
  type Target = str;
  fn deref(&self) -> &Self::Target {
    self.as_ref()
  }
}
impl PartialEq for MyString {
  fn eq(&self, other: &Self) -> bool {
    self.bytes == other.bytes
  }
}
impl Eq for MyString {}

impl PartialOrd for MyString {
  fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
    Some(self.bytes.cmp(&other.bytes))
  }
}

impl Ord for MyString {
  fn cmp(&self, other: &Self) -> std::cmp::Ordering {
    self.partial_cmp(other).expect("")
  }
}
impl std::fmt::Display for MyString {
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
    write!(f, "{}", self.as_str())
  }
}
// impl Index<usize> for MyString {
//   type Output = u32;
//   fn index(&self, index: usize) -> &Self::Output {
//     let mut ch = 0_u32;
//     if index == self.len() - 1 {
//       let &begin = self.offsets.last().expect("");
//       self.bytes[begin..].iter().for_each(|&x| {
//         ch <<= 8;
//         ch += x as u32;
//       });
//     } else {
//       let begin = self.offsets[index];
//       let end = self.offsets[index + 1];
//       self.bytes[begin..end].iter().for_each(|&x| {
//         ch <<= 8;
//         ch += x as u32;
//       });
//     }
//     &ch
//   }
// }

#[cfg(test)]
mod tests {
  use crate::my_string::MyString;

  #[test]
  fn temp_test() {
    let a = 'a';
    let b = a as u8;
    println!("{}", b);
  }

  #[test]
  fn test_new() {
    let s = String::new();
    let my_s = MyString::new();
    let s = s.as_str();
    let ss = my_s.as_str();
    assert_eq!(MyString::convert_char('世'), "世".as_bytes());
    assert_eq!(MyString::convert_char('😀'), "😀".as_bytes());
  }
  #[test]
  fn test_push() {
    let mut my_s = MyString::new();
    my_s.push_char('a');
    my_s.push_str("是utf-8字符");
    println!("{}", my_s);
    assert_eq!(my_s.as_str(), "a是utf-8字符");
  }
  #[test]
  fn test_insert() {
    let mut my_s = MyString::from("hllo, ");
    my_s.insert_char(1, 'e');
    my_s.insert_char(7, '世');
    my_s.insert_char(8, '界');
    my_s.insert_char(6, '😀');
    assert_eq!(my_s.as_str(), "hello,😀 世界");
    my_s.insert_str(8, "这是");
    assert_eq!(my_s.as_str(), "hello,😀 这是世界");
  }
  #[test]
  fn test_index() {
    let my_s = MyString::from("hello, 世界");
    assert_eq!(Some('e'), my_s.get(1));
    assert_eq!(Some('世'), my_s.get(7));
  }
}
