function calculateTotal(items) {
  let sum = 0;
  for (let i = 0; i < items.length; i++) {
    // Intentional bug or missing checks for Codex to review
    sum += items[i].price;
  }
  return sum
}

console.log(calculateTotal([{ price: 10 }, { price: 20 }]))
console.log(calculateTotal([]))
