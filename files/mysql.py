import subprocess
from datetime import datetime

# Some output
red = '\033[0;31m'
green = '\033[0;32m'
nc = '\033[0m'
line = '\n' + ('=' * 50) + "\n"


def error_generator(type, error_msg):
    # Return based on dictionary, because switch was introduced in Python 3.10,
    # so it may be unavailable on some servers.
    return {
        'dump_error': f'{line}Couldn\'t dump because\n{red}{error_msg}{nc}Aborting{line}',
        'archvie_error': f'{line}Couldn\'t archive because\n{red}{error_msg}{nc}Aborting{line}'
    }.get(type, f'{line}{red}Generic error!{nc}{line}')


def status_report(results):
    # Summary whole backup job
    for RESULT in results:
        if type(RESULT) == str:
            print(f'{line}{green}{RESULT}{nc}\nHave been successfully backedup{line}')


def archive(archive_cmd, result_sql):
    return subprocess.run(archive_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=True,
                             input=result_sql,
                             encoding='ascii')

def create_backup(ip, port, user, password, db):
    now = datetime.today()
    # Prefix YYYY-M-D_H:M
    prefix = f'{now.year}-{now.month}-{now.day}_{now.hour}:{now.minute}'
    filename = f'mysql/{prefix}-{db}.sql.gz'
    # Prepare dump command
    dump = f'/opt/homebrew/opt/mysql-client/bin/mysqldump' \
           f' --single-transaction' \
           f' --column-statistics=0' \
           f' --host {ip}' \
           f' --port {port}' \
           f' --user {user}' \
           f' -p' \
           f' {db}'
    # Prepare archive command
    archive_cmd = f'pigz -9 > {filename}'

    result = subprocess.run(dump,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            input=password,
                            encoding='ascii')
    # Assume that error occurred, when exit code is not 0
    if result.returncode != 0:
        print(error_generator("dump_error", result.stderr.strip("Enter password: ")))
        return 1

    archive_result = archive(archive_cmd=archive_cmd, result_sql=result.stdout)

    if archive_result.returncode != 0:
        # Try to fall back to gzip
        archive_cmd = f'gzip -9 > {filename}'
        archive_result = archive(archive_cmd=archive_cmd, result_sql=result.stdout)
        if archive_result.returncode != 0:
            print(error_generator('archive_error', archive_result.stderr))
            return 1

    return filename


def read_config(filename):
    # Variable initialization, so the code is easier to read
    ip = []
    port = []
    user = []
    password = []
    db = []
    lines = 0

    with open(filename, "r") as config:
        # First iterate over each line in file, and put values from config to proper lists
        for val in config.readlines():
            val = val.strip("\n").split(";")
            ip.append(val[0])
            port.append(val[1])
            user.append(val[2])
            password.append(val[3])
            db.append(val[4])
            lines += 1

    return ip, port, user, password, db, lines


def main():
    filename = 'config'
    ip, port, user, password, db, lines = read_config(filename)
    archives = []
    for i in range(0, lines):
        archives.append(create_backup(ip[i], port[i], user[i], password[i], db[i]))
    status_report(archives)


if __name__ == '__main__':
    main()
