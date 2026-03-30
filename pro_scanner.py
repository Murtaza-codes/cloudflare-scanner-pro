import socket
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.align import Align

console = Console()

BRANDING = """[bold cyan]Cloudflare Advanced Scanner[/bold cyan]
[dim]By github.com/murtaza-codes | murtaza.website[/dim]"""

LANGUAGES = {
    "1": {
        "name": "English",
        "region_prompt": "Select Target Region",
        "regions": {"1": "China (Optimized)", "2": "Global", "3": "Russia"},
        "port_prompt": "Enter target port",
        "count_prompt": "How many IPs to scan? (e.g., 100 to 10000)",
        "start": "🚀 Starting scan on port {port} for {region}...",
        "scanning": "Scanning IPs...",
        "top_ips": "🏆 Top Clean IPs with lowest latency",
        "no_results": "❌ No clean IPs found. Network might be heavily disrupted.",
        "ip_col": "IP Address",
        "delay_col": "Latency (ms)",
        "status_col": "Status",
        "save_prompt": "Do you want to save the top 10 IPs to a text file?",
        "save_success": "✅ Results saved to {file}",
        "continue_prompt": "Press [ENTER] to return to the main menu...",
        "exit_msg": "Exiting program. Goodbye!"
    },
    "2": {
        "name": "中文",
        "region_prompt": "选择目标地区",
        "regions": {"1": "中国 (优化)", "2": "全球", "3": "俄罗斯"},
        "port_prompt": "输入目标端口",
        "count_prompt": "要扫描多少个 IP？(例如 100 到 10000)",
        "start": "🚀 开始在端口 {port} 上扫描 {region}...",
        "scanning": "正在扫描 IP...",
        "top_ips": "🏆 延迟最低的可用 IP",
        "no_results": "❌ 未找到可用的 IP。网络可能受到严重干扰。",
        "ip_col": "IP 地址",
        "delay_col": "延迟 (ms)",
        "status_col": "状态",
        "save_prompt": "是否将前 10 个 IP 保存到文本文件中？",
        "save_success": "✅ 结果已保存到 {file}",
        "continue_prompt": "按 [回车键] 返回主菜单...",
        "exit_msg": "退出程序。再见！"
    },
    "3": {
        "name": "Русский",
        "region_prompt": "Выберите целевой регион",
        "regions": {"1": "Китай (оптимизировано)", "2": "Глобальный", "3": "Россия"},
        "port_prompt": "Введите целевой порт",
        "count_prompt": "Сколько IP-адресов сканировать? (от 100 до 10000)",
        "start": "🚀 Запуск сканирования на порту {port} для {region}...",
        "scanning": "Сканирование IP-адресов...",
        "top_ips": "🏆 Чистые IP-адреса с наименьшей задержкой",
        "no_results": "❌ Чистые IP-адреса не найдены.",
        "ip_col": "IP-адрес",
        "delay_col": "Задержка (мс)",
        "status_col": "Статус",
        "save_prompt": "Хотите сохранить топ-10 IP в текстовый файл?",
        "save_success": "✅ Результаты сохранены в {file}",
        "continue_prompt": "Нажмите [ENTER], чтобы вернуться в главное меню...",
        "exit_msg": "Выход из программы. До свидания!"
    }
}

IP_RANGES = {
    "1": ["104.16", "104.17", "104.18", "104.19", "172.64", "172.67", "162.159", "104.20"],
    "2": ["173.245", "103.21", "103.22", "103.31", "104.15", "141.101", "108.162", "190.93", "188.114", "197.234", "198.41", "162.158"],
    "3": ["104.21", "172.67", "188.114", "104.16", "162.159"]
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_ips(region_key, count):
    subnets = IP_RANGES[region_key]
    ips = set()
    while len(ips) < count:
        sub = random.choice(subnets)
        ip = f"{sub}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        ips.add(ip)
    return list(ips)

def scan_ip(ip, port):
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.2)
        result = sock.connect_ex((ip, port))
        end = time.time()
        sock.close()

        if result == 0:
            latency = round((end - start) * 1000, 2)
            return (ip, latency)
    except Exception:
        pass
    return None

def main_menu():
    clear_screen()
    console.print(Panel(Align.center(BRANDING), border_style="cyan"))
    
    console.print("[bold yellow]Select Language / 选择语言 / Выберите язык:[/bold yellow]")
    console.print("1. English")
    console.print("2. 中文 (Chinese)")
    console.print("3. Русский (Russian)")
    
    lang_choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="1")
    lang = LANGUAGES[lang_choice]

    while True:
        clear_screen()
        console.print(Panel(Align.center(BRANDING), border_style="cyan"))
        
        console.print(f"\n[bold green]{lang['region_prompt']}:[/bold green]")
        for key, val in lang["regions"].items():
            console.print(f"{key}. {val}")
        
        region_choice = Prompt.ask("Region", choices=["1", "2", "3"], default="1")
        region_name = lang["regions"][region_choice]

        port = IntPrompt.ask(f"\n[bold yellow]{lang['port_prompt']}[/bold yellow]", default=443)

        count = IntPrompt.ask(f"\n[bold magenta]{lang['count_prompt']}[/bold magenta]", default=500)

        ips = generate_ips(region_choice, count)
        results = []

        console.print(f"\n[bold cyan]{lang['start'].format(port=port, region=region_name)}[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(f"[cyan]{lang['scanning']}", total=len(ips))
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                future_to_ip = {executor.submit(scan_ip, ip, port): ip for ip in ips}
                
                for future in as_completed(future_to_ip):
                    res = future.result()
                    if res:
                        results.append(res)
                    progress.advance(task)

        results.sort(key=lambda x: x[1])

        if results:
            table = Table(title=lang["top_ips"], title_style="bold magenta", border_style="cyan")
            table.add_column(lang["ip_col"], justify="center", style="cyan", no_wrap=True)
            table.add_column(lang["delay_col"], justify="center", style="green")
            table.add_column(lang["status_col"], justify="center")

            top_results = results[:10]
            for ip, delay in top_results:
                delay_style = "green" if delay < 150 else "yellow" if delay < 300 else "red"
                table.add_row(ip, f"[{delay_style}]{delay}[/{delay_style}]", f"✅ [bold green]Port {port}[/bold green]")

            console.print()
            console.print(table)
            
            console.print()
            if Confirm.ask(f"[bold yellow]{lang['save_prompt']}[/bold yellow]"):
                filename = f"clean_ips_{region_name.split()[0]}_{port}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"--- Clean IPs for {region_name} | Port: {port} ---\n")
                    f.write("By github.com/murtaza-codes | murtaza.website\n\n")
                    for ip, delay in top_results:
                        f.write(f"{ip}:{port} - Delay: {delay}ms\n")
                
                console.print(f"\n[bold green]{lang['save_success'].format(file=filename)}[/bold green]")

        else:
            console.print(f"\n[bold red]{lang['no_results']}[/bold red]")

        console.print("\n" + "="*40)
        try:
            Prompt.ask(f"[bold cyan]{lang['continue_prompt']}[/bold cyan]")
        except KeyboardInterrupt:
            console.print(f"\n[bold red]{lang['exit_msg']}[/bold red]")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold red]Program terminated by user.[/bold red]")
