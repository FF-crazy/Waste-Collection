function maxProfit(prices: number[], strategy: number[], k: number): number {
  const n = prices.length;
  let prefix: number[] = Array(n + 1);
  let allSold: number[] = Array(n + 1);
  prefix[0] = 0;
  allSold[0] = 0;
  for (let i = 0; i < n; i++) {
    prefix[i + 1] = prefix[i] + prices[i] * strategy[i];
    allSold[i + 1] = allSold[i] + prices[i];
  }
  const m = prefix[n];
  let ans = Number.MIN_VALUE;
  for (let i = k / 2 - 1; i < n - k / 2; i++) {
    let temp = m - (prefix[i + k / 2 + 1] - prefix[i + 1 - k / 2]);
    temp += allSold[i + k / 2 + 1] - allSold[i + 1];
    ans = Math.max(ans, temp);
  }
  let array: number[] = [];
  array.push(123);

};