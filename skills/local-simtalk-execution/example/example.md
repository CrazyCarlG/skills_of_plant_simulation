# Example: Using socket_client.py

## Send Ping Data

```
python3 socket_client.py --port 9000 --data '{"type":"ping","timestamp":"20260824170056"}||END||'
```

Server response

```
{"type":"result","result":"success"}
```

如果网络不通，则无法收到回复。

## Send simtalk_syntax

```
python3 socket_client.py --port 9000 --data '{"type":"simtalk_syntax","action_id":"64kashjitppqinmvisahf","simtalk":"print \"hello world\""}||END||'
```

Server response

```
{
    "type":"action_result",
    "action_id":"64kashjitppqinmvisahf",
    "result":"failed",
    "log":"the code has syntax error in line 2"
}||END||
```

## Send simtalk_run

```
python3 socket_client.py --port 9000 --data '{"type":"simtalk_run","action_id":"64kashjitppqinmvisahf","expression":"print \"hello world\""}||END||'
```

Server response

```
{
    "type":"action_result",
    "action_id":"64kashjitppqinmvisahf",
    "result":"failed",
    "log":"the code has execute error in line 2"
}||END||
```
