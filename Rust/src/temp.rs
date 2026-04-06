use std::collections::HashMap;
struct RangeFreqQuery {
  counter: HashMap<i32, Vec<usize>>,
}


/** 
 * `&self` means the method takes an immutable reference.
 * If you need a mutable reference, change it to `&mut self` instead.
 */
impl RangeFreqQuery {

    fn new(arr: Vec<i32>) -> Self {
        let n = arr.len() / 10;
        let mut counter = HashMap::new();
        for (i, &item) in arr.iter().enumerate() {
          counter.entry(item).or_insert_with(|| {Vec::with_capacity(n)}).push(i);
        }
        RangeFreqQuery { counter }
    }
    
    fn query(&self, left: i32, right: i32, value: i32) -> i32 {
        if let Some(count) = self.counter.get(&value) {
          let lower = count.partition_point(|&x| {x < left as usize});
          let upper = count.partition_point(|&x| {x < (right + 1) as usize});
          (upper - lower) as _
        } else {
          0
        }
        
    }
}

/**
 * Your RangeFreqQuery object will be instantiated and called as such:
 * let obj = RangeFreqQuery::new(arr);
 * let ret_1: i32 = obj.query(left, right, value);
 */

#[test]
fn test() {

}