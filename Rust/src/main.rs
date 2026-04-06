
pub struct Solution;


fn main() {
    let s = "10101".to_string();
    println!("{}", Solution::count_k_constraint_substrings(s, 1));
}
