class: center, middle, inverse

# Using Markdown to create a presentation
<img src="logo.png" height="85" width="300" />

.footnote[This slide deck was created with [Remark](https://github.com/gnab/remark)]

???
Here are some presenter notes

---
# Lists

### Here is a order list:

1. Red
2. Blue
3. Green
4. Yellow

### Here is an unordered list:

- Pink
- Purple
- Magenta
- Brown

???
More presenter nodes goes here

---
# Remark handles Code and Tables

###Check out this code:

```python
def passwordGen(plength):
    chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!'
    p = []
    for char in range(plength):
        p.append(random.choice(chars))
    return(''.join(p))
```

###Here is a table:


| Product  | Color    | Cost  |
|:-------- |:-------- | -----:|
| One      | Blue     | $1600 |
| Two      | Green    |   $12 |
| Three    | Yellow   |    $1 |

---

class: center, middle, inverse
# THE END