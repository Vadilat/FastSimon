# FastSimo

## Live App
**Live App URL**: https://fastsimon-455407.ew.r.appspot.com/

## Task II: Variable Commands Example:

| Route                 | Description                             |
|-----------------------|-----------------------------------------|
| `/set?name=x&value=5` | Sets `x = 5`                            |
| `/get?name=x`         | Returns value of `x`, or `None`         |
| `/unset?name=x`       | Deletes variable `x`                    |
| `/numequalto?value=5` | Returns number of variables set to `5`  |
| `/undo`               | Undoes last `SET` or `UNSET`            |
| `/redo`               | Redoes the last undone command          |
| `/end`                | Cleans the database (removes all data)  |
| `/list`               | Lists all variables and their values    |

### Bonus Feature – `list` Endpoint (Question 6)
**Endpoint:**  
`/list`  
**Description:**  
Lists all currently defined variables and their values.
**Example Response:**
```json
{
  "a": "10",
  "b": "20",
  "c": "30"
}