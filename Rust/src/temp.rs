use std::collections::VecDeque;
struct Router {
  deque: VecDeque<(i32, i32, i32)>,
  mem: usize,
}


/** 
 * `&self` means the method takes an immutable reference.
 * If you need a mutable reference, change it to `&mut self` instead.
 */
impl Router {

    fn new(memoryLimit: i32) -> Self {
        Router { deque: VecDeque::with_capacity(memoryLimit as usize), mem: memoryLimit as _ }
    }
    
    fn add_packet(&mut self, source: i32, destination: i32, timestamp: i32) -> bool {
      for &item in self.deque.iter().rev() {
        if item.2 != timestamp {
          break;
        }
        if item.0 == source && item.1 == destination {
          return false;
        }
      }
      if self.deque.len() == self.mem {
        self.deque.pop_front();
      }
      self.deque.push_back((source, destination, timestamp));
      return true;
    }
    
    fn forward_packet(&mut self) -> Vec<i32> {
        if let Some(item) = self.deque.pop_front() {
          vec![item.0, item.1, item.2]
        } else {
          Vec::new()
        }
    }
    
    fn get_count(&self, destination: i32, start_time: i32, end_time: i32) -> i32 {
        let left = self.deque.partition_point(|&x| {x.2 < start_time});
        let right = self.deque.partition_point(|&x| {x.2 <= end_time}) as i32 - 1;
        if right == -1 {
          return 0;
        }
        let mut ans = 0;
        for item in left..=right as usize {
          if self.deque[item].1 == destination {
            ans += 1;
          }
        }
        ans
    }
}