from pathlib import Path
import zipfile
import requests  # type: ignore

base_url = "https://vip.123pan.cn/1820333155/extensions_website/addons_zip/"

def download_zip(save_folder):
    folder_name = save_folder.name
    zip_name = f"{folder_name}.zip"
    url = base_url + zip_name
    save_path = save_folder / zip_name
    marker_file = save_folder / f"{folder_name}.downloaded_marker"
    # 检查标识文件是否存在，存在则跳过下载和解压
    if marker_file.exists():
        print(f"{zip_name} 已经下载并解压，跳过操作。")
        return
    # 下载文件
    headers = {
        "Accept": "application/zip, application/json, text/html, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    f.write(chunk)
        # 解压文件并保留目录结构
        with zipfile.ZipFile(save_path, "r") as zip_ref:
            zip_ref.extractall(save_folder)
        # 创建标识文件
        marker_file.touch()
        # 删除下载的zip文件
        if save_path.exists():
            save_path.unlink()
    except requests.exceptions.RequestException as e:
        print(f"下载文件时发生错误(请检查网络)：{e}")

def downloading():
    down_path = Path(__file__).parent
    download_zip(down_path)
