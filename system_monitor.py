#!/usr/bin/env python3
"""
System Monitor - Скрипт для мониторинга ресурсов системы
"""

import sys
import psutil
import datetime
import json
import os
from pathlib import Path


def check_os():
    """Проверить операционную систему"""
    if sys.platform != "linux":
        print(f"Ошибка: скрипт предназначен только для Linux")
        print(f"Текущая ОС: {sys.platform}")
        sys.exit(1)


def check_root():
    """Проверить права root"""
    if os.geteuid() != 0:
        print(f"Ошибка: скрипт требует прав root")
        print(f"Запустите от имени root (sudo)")
        sys.exit(1)


def get_cpu_info():
    """Получить информацию о CPU"""
    return {
        "percent": psutil.cpu_percent(interval=1),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }


def get_memory_info():
    """Получить информацию о памяти"""
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "percent": memory.percent,
        "used": memory.used,
        "free": memory.free
    }


def get_disk_info():
    """Получить информацию о дисках"""
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })
        except PermissionError:
            continue
    return disks


def get_network_info():
    """Получить информацию о сети"""
    net_io = psutil.net_io_counters()
    return {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv
    }


def get_process_info(top_n=5):
    """Получить информацию о топ-N процессах по использованию CPU"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    return processes[:top_n]


def format_bytes(bytes_value):
    """Форматировать байты в человекочитаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def generate_report():
    """Сгенерировать полный отчет о системе"""
    timestamp = datetime.datetime.now().isoformat()
    
    report = {
        "timestamp": timestamp,
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "network": get_network_info(),
        "top_processes": get_process_info()
    }
    
    return report


def print_report(report):
    """Вывести отчет в консоль"""
    print("=" * 60)
    print(f"ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ")
    print(f"Время: {report['timestamp']}")
    print("=" * 60)
    
    # CPU
    cpu = report['cpu']
    print(f"\n📊 CPU:")
    print(f"   Загрузка: {cpu['percent']}%")
    print(f"   Ядра: {cpu['cores_physical']} физических / {cpu['cores_logical']} логических")
    if cpu['freq']:
        print(f"   Частота: {cpu['freq']['current']:.2f} MHz")
    
    # Memory
    mem = report['memory']
    print(f"\n💾 Память:")
    print(f"   Загрузка: {mem['percent']}%")
    print(f"   Использовано: {format_bytes(mem['used'])} / {format_bytes(mem['total'])}")
    print(f"   Свободно: {format_bytes(mem['free'])}")
    
    # Disk
    print(f"\n💿 Диски:")
    for disk in report['disk']:
        print(f"   {disk['device']} ({disk['mountpoint']}):")
        print(f"      Загрузка: {disk['percent']}%")
        print(f"      Использовано: {format_bytes(disk['used'])} / {format_bytes(disk['total'])}")
    
    # Network
    net = report['network']
    print(f"\n🌐 Сеть:")
    print(f"   Отправлено: {format_bytes(net['bytes_sent'])} ({net['packets_sent']} пакетов)")
    print(f"   Получено: {format_bytes(net['bytes_recv'])} ({net['packets_recv']} пакетов)")
    
    # Top Processes
    print(f"\n🔝 Топ процессов по CPU:")
    for i, proc in enumerate(report['top_processes'], 1):
        print(f"   {i}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']}%, Mem: {proc['memory_percent']}%")
    
    print("\n" + "=" * 60)


def save_report(report, filepath="system_monitor_report.json"):
    """Сохранить отчет в JSON файл"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✓ Отчет сохранен в {filepath}")


def check_installed_packages(output_file="monitor_logs/list_lib.log"):
    """
    Проверить все установленные Python-библиотеки и сохранить список в файл

    Args:
        output_file: Путь к файлу для сохранения списка библиотек
    """
    import subprocess

    # Получаем список установленных пакетов через pip
    result = subprocess.run(
        ["pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    # Формируем содержимое файла
    lines = []
    lines.append("Список установленных Python-библиотек")
    lines.append(f"Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    if result.returncode == 0:
        packages = result.stdout.strip().split('\n')
        lines.append(f"Всего пакетов: {len(packages)}")
        lines.append("=" * 60)
        lines.extend(packages)
    else:
        lines.append(f"Ошибка получения списка пакетов: {result.stderr}")

    # Создаем директорию если не существует
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Записываем в файл
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✓ Список библиотек сохранен в {output_path.absolute()}")
    return str(output_path)


def create_directory_with_listing(dir_path="monitor_logs"):
    """
    Создать каталог, в нем файл test.log и записать листинг каталога

    Args:
        dir_path: Путь к создаваемому каталогу (по умолчанию 'monitor_logs')
    """
    # Создаем каталог
    directory = Path(dir_path)
    directory.mkdir(parents=True, exist_ok=True)
    print(f"✓ Каталог создан: {directory.absolute()}")
    
    # Создаем файл test.log
    log_file = directory / "test.log"
    
    # Получаем листинг каталога
    listing_lines = []
    listing_lines.append(f"Листинг каталога: {directory.absolute()}")
    listing_lines.append(f"Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    listing_lines.append("=" * 60)
    
    try:
        entries = os.listdir(directory)
        if entries:
            for entry in sorted(entries):
                full_path = directory / entry
                if full_path.is_file():
                    size = full_path.stat().st_size
                    listing_lines.append(f"  [FILE] {entry} ({size} байт)")
                elif full_path.is_dir():
                    listing_lines.append(f"  [DIR]  {entry}/")
        else:
            listing_lines.append("  (каталог пуст)")
    except PermissionError as e:
        listing_lines.append(f"  Ошибка доступа: {e}")
    
    # Записываем листинг в файл
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(listing_lines))
    
    print(f"✓ Файл создан: {log_file.absolute()}")
    print(f"✓ В файл записан листинг каталога")
    
    return str(log_file)


def main():
    """Основная функция"""
    check_os()
    # check_root()
    report = generate_report()
    print_report(report)
    save_report(report)
    create_directory_with_listing()
    check_installed_packages()


if __name__ == "__main__":
    main()
