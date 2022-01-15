# Client Server File Transfer Application 

A FTP Server and Client architecture with ARQ schemes (Go Back N, Selective Repeat) in Python utilizing Socket Programming. Maintained multi-threaded model to simultaneously buffer and manage the packet received and transferred

## Environment

The following Environment was used to execute the codes

- macOS Big Sur Version 11.6 (20G165)
- Python 3.7.4

## Procedure

### Go-back-N Automatic Repeat Request (ARQ)

First run Server by running the command:
```
python3 Simple_ftp_server.py <port#> <file_name> <p>

For example: python3 Simple_ftp_server.py 7735 output.txt 0.01
```

After that run Client by running the command:
```
python3 Simple_ftp_client.py <server-host-name> <server-port#> <file-name> <N> <MSS>

For example: python3 Simple_ftp_client.py ABCs-MBP.lan 7735 input.txt 1 1000
```

### Selective Repeat Automatic Repeat Request (ARQ)

First run Server by running the command:
```
python3 Selective_Repeat_Simple_ftp_server.py <port#> <file_name> <p>

For example: python3 Selective_Repeat_Simple_ftp_server.py 7735 output.txt 0.01
```

After that run Client by running the command:
```
python3 Selective_Repeat_Simple_ftp_client.py <server-host-name> <server-port#> <file-name> <N> <MSS>

For example: python3 Selective_Repeat_Simple_ftp_client.py ABCs-MBP.lan 7735 input.txt 1 1000
```
