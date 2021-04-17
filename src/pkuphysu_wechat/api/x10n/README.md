# 数量级估算大赛部分

## 2020 年的要求

积分赛制的话，我们希望给您这边充足数量的单选题作为题库，您随机抽取生成各组题目（每组题目数量相同），交给参赛同学答题。每题限定一定时间，若未在限定时间内完成则视为错误，提前完成并提交则进入下一题，直至同学答完所有题目。希望这里可以记录同学们的总答题时间，以便在答对题数相同时按照总时间排名。

## 大致流程

1. 访问 Auth Portal 带参数 `/?page=x10n` 完成微信授权
2. 要求输入姓名和微信号，向后端 `/api/x10n` 发送 GET 请求。如果没有参加过，则继续，否则到 6
3. 呈现题目，并设置 timeout，超过则强制提交。提交后显示正误并抽取下一题，清空 timeout
4. 重复 3 直至题目答完。
5. POST 答案给服务器 `/api/x10n`
6. 显示服务器返回的答题汇总结果

## API 格式暂定

### `GET /api/x10n`

Returns:
```js
{
  played: true,
  result: {
    time: 100,
    questions: [
      {
        number: 3,
        answer: true
      }
    ]
  }
}
```

```js
{
  played: false,
  questions: [
    {
      number: 0,
      text: 'xx 的数量级是？',
      img: 'https://tuchuang...',
      choices: ['一个月', '半年']
    }
  ]
}
```

注意如果参加一次没答完就退出，算参加过没成绩，故 `played` 为 `true` 不代表有 `result`

### `POST /api/x10n`

Body:
```js
result: {
  name: 'zhangsan',
  wx: 'wxid_jkahg',
  questions: [
    {
      number: 3,
      answer: 1 // A = 0, B = 1 ...
    }
  ]
}
```

Returns:
```js
{
  msg: 'success',
  result: {
    time: 100,
    questions: [
      {
        number: 3,
        answer: true
      }
    ]
  }
}
```

## 主要变动

参见 <https://github.com/pkuphysu/x10n>

1. 增加了微信的授权，去掉了学号
2. 题目乱序、答题成绩、时间的记录由后端给出
