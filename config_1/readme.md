# Создание виртуальной файловой системы
```
mkdir -p vfs/home/user

mkdir -p vfs/var/log

mkdir -p vfs/etc
 
echo "Hello, World!" > vfs/home/user/file1.txt

echo "This is a test file." > vfs/home/user/file2.txt

echo "System log content..." > vfs/var/log/syslog

echo "Configuration file." > vfs/etc/config.cfg

cd vfs/home/user

nano file3.txt
1
2
3
4
5
6
7
8
9
10
tar -cvf filesystem.tar -C vfs .
```
# Запуск работы
python3 emulator.py -n mypc -f filesystem.tar -s startup.sh
