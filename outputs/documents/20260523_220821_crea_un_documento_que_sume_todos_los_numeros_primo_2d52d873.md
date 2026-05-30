```python
primos = [2]
for num in range(3, 101, 2):
    if all(num % p > 0 for p in primos):
        primos.append(num)
print(sum(primos))
```