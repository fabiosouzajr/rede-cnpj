# -*- coding: utf-8 -*-
"""
Download de arquivos de dados eleitorais do TSE
Portal de Dados Abertos do TSE: https://dadosabertos.tse.jus.br/dataset/?groups=candidatos
"""

from bs4 import BeautifulSoup
import requests
import os
import sys
import time
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

BASE_URL = 'https://dadosabertos.tse.jus.br'
CANDIDATOS_URL = f'{BASE_URL}/dataset/?groups=candidatos'
PASTA_BASE = 'dados-tse'

# Headers para evitar bloqueio
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}


def setup_directories(base_dir=PASTA_BASE, year=None):
    """Cria diretórios necessários"""
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    
    if year:
        year_dir = os.path.join(base_dir, str(year))
        if not os.path.isdir(year_dir):
            os.makedirs(year_dir)
        return year_dir
    return base_dir


def get_election_years(base_url=BASE_URL):
    """
    Extrai todos os anos de eleição disponíveis da página principal
    Retorna lista de tuplas: [(ano, url), ...] ordenada por ano (mais recente primeiro)
    """
    print(time.asctime(), 'Buscando anos de eleição disponíveis...')
    
    try:
        response = requests.get(CANDIDATOS_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        years_data = []
        
        # Encontrar todos os links que contêm "Candidatos -" seguido de um ano
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Procurar padrão "Candidatos - YYYY"
            if 'Candidatos' in text and any(c.isdigit() for c in text):
                # Extrair o ano (últimos 4 dígitos no texto)
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', text)
                if year_match:
                    year = int(year_match.group())
                    # Construir URL completa
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Evitar duplicatas
                    if (year, full_url) not in years_data:
                        years_data.append((year, full_url))
        
        # Ordenar por ano (mais recente primeiro)
        years_data.sort(key=lambda x: x[0], reverse=True)
        
        print(f'Encontrados {len(years_data)} anos de eleição')
        return years_data
        
    except requests.RequestException as e:
        print(f'Erro ao buscar anos de eleição: {e}')
        sys.exit(1)


def get_resources_from_year(year_url, year):
    """
    Extrai todos os recursos (arquivos) de uma página de ano específico
    Retorna lista de dicionários: [{'name': '...', 'url': '...', 'format': '...', 'size': '...'}, ...]
    """
    try:
        response = requests.get(year_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        resources = []
        
        # Encontrar a seção "Dados e recursos"
        dados_section = soup.find('h2', string=lambda x: x and 'dados' in x.lower() and 'recursos' in x.lower())
        
        if not dados_section:
            print(f'  Aviso: Seção "Dados e recursos" não encontrada para {year}')
            return resources
        
        # Encontrar todos os itens de recurso
        resource_items = soup.find_all('li', class_=lambda x: x and 'resource' in str(x).lower())
        
        print(f'  Encontrados {len(resource_items)} recursos para {year}')
        
        for res_item in resource_items:
            try:
                # Obter título do recurso
                title_elem = res_item.find(['h3', 'h4', 'a'], class_=lambda x: x and 'heading' in str(x).lower())
                if not title_elem:
                    title_elem = res_item.find('a', href=True)
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Encontrar link "Ir para recurso" que contém a URL de download
                ir_recurso_link = res_item.find('a', string=lambda x: x and 'ir para recurso' in x.lower())
                
                if not ir_recurso_link:
                    # Tentar encontrar qualquer link que pareça ser de download
                    download_links = res_item.find_all('a', href=True)
                    for link in download_links:
                        href = link.get('href', '')
                        # Verificar se é uma URL externa (provavelmente download)
                        if href.startswith('http') and ('cdn.tse.jus.br' in href or 'download' in href.lower()):
                            ir_recurso_link = link
                            break
                
                if not ir_recurso_link:
                    print(f'    Aviso: Link de download não encontrado para "{title[:50]}"')
                    continue
                
                download_url = ir_recurso_link.get('href', '')
                
                # Se a URL não parece ser um link direto de download, seguir para a página do recurso
                if download_url and not download_url.endswith(('.zip', '.csv', '.pdf', '.txt', '.xlsx', '.xls', '.jpg', '.jpeg')):
                    # Pode ser um link para a página do recurso, tentar seguir
                    if download_url.startswith('/') or 'dataset' in download_url:
                        resource_page_url = urljoin(BASE_URL, download_url)
                        try:
                            res_response = requests.get(resource_page_url, headers=HEADERS, timeout=30)
                            res_response.raise_for_status()
                            res_soup = BeautifulSoup(res_response.text, 'lxml')
                            # Procurar link de download direto na página do recurso
                            direct_download = res_soup.find('a', href=lambda x: x and (
                                x.endswith(('.zip', '.csv', '.pdf', '.txt', '.xlsx', '.xls', '.jpg', '.jpeg')) or
                                'download' in x.lower() or 'cdn.tse.jus.br' in x
                            ))
                            if direct_download:
                                download_url = direct_download.get('href', '')
                                if download_url.startswith('/'):
                                    download_url = urljoin(BASE_URL, download_url)
                        except:
                            pass  # Se falhar, usar a URL original
                
                # Limpar URL (remover trailing dots, espaços, etc)
                download_url = download_url.rstrip('. \n\r\t')
                
                # Extrair formato do arquivo (se disponível no título ou URL)
                file_format = 'unknown'
                if download_url:
                    parsed = urlparse(download_url)
                    path = parsed.path.lower()
                    if path.endswith('.zip'):
                        file_format = 'ZIP'
                    elif path.endswith('.csv'):
                        file_format = 'CSV'
                    elif path.endswith('.pdf'):
                        file_format = 'PDF'
                    elif path.endswith('.txt'):
                        file_format = 'TXT'
                    elif path.endswith(('.xlsx', '.xls')):
                        file_format = 'XLSX'
                    elif path.endswith(('.jpg', '.jpeg')):
                        file_format = 'JPEG'
                
                # Tentar obter tamanho do arquivo (se disponível)
                file_size = None
                size_elem = res_item.find(string=lambda x: x and ('mb' in x.lower() or 'kb' in x.lower() or 'gb' in x.lower()))
                if size_elem:
                    file_size = size_elem.strip()
                
                # Gerar nome do arquivo
                filename = os.path.basename(urlparse(download_url).path)
                if not filename or filename == '/':
                    # Usar título como base para o nome do arquivo
                    import re
                    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
                    safe_title = re.sub(r'[-\s]+', '-', safe_title)
                    filename = f"{safe_title}.{file_format.lower()}"
                
                resources.append({
                    'name': filename,
                    'title': title,
                    'url': download_url,
                    'format': file_format,
                    'size': file_size
                })
                
            except Exception as e:
                print(f'    Erro ao processar recurso: {e}')
                continue
        
        return resources
        
    except requests.RequestException as e:
        print(f'  Erro ao buscar recursos para {year}: {e}')
        return []


def download_file(url, output_path, show_progress=True):
    """
    Baixa um arquivo com barra de progresso
    Retorna (success, error_message)
    """
    try:
        # Verificar se arquivo parcial existe para retomar download
        resume_header = {}
        if os.path.exists(output_path):
            resume_header['Range'] = f'bytes={os.path.getsize(output_path)}-'
        
        response = requests.get(url, headers={**HEADERS, **resume_header}, stream=True, timeout=60)
        
        # Se servidor não suporta Range, começar do zero
        if response.status_code == 416:  # Range Not Satisfiable
            resume_header = {}
            response = requests.get(url, headers=HEADERS, stream=True, timeout=60)
        
        response.raise_for_status()
        
        # Obter tamanho total
        total_size = int(response.headers.get('content-length', 0))
        if resume_header and os.path.exists(output_path):
            total_size += os.path.getsize(output_path)
        
        # Modo de escrita
        mode = 'ab' if resume_header and os.path.exists(output_path) else 'wb'
        
        filename = os.path.basename(output_path)
        
        with open(output_path, mode) as f:
            if show_progress:
                with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, 
                          desc=filename[:50], initial=os.path.getsize(output_path) if mode == 'ab' else 0) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        return (True, None)
        
    except requests.RequestException as e:
        return (False, str(e))
    except Exception as e:
        return (False, str(e))


def prompt_year_selection(available_years):
    """
    Solicita ao usuário seleção de anos
    Retorna lista filtrada de (ano, url) tuplas
    """
    print('\n' + '='*60)
    print('Anos de eleição disponíveis:')
    print('='*60)
    for i, (year, url) in enumerate(available_years, 1):
        print(f'{i:3d}. {year}')
    print('='*60)
    
    while True:
        choice = input('\nEscolha uma opção:\n'
                      '  - "all" ou "a" para baixar todos os anos\n'
                      '  - "last N" ou "l N" para baixar os últimos N anos (ex: "last 10")\n'
                      '  - Números separados por vírgula para selecionar anos específicos (ex: "1,3,5")\n'
                      'Sua escolha: ').strip().lower()
        
        if choice in ['all', 'a']:
            return available_years
        
        if choice.startswith('last ') or choice.startswith('l '):
            try:
                n = int(choice.split()[-1])
                return available_years[:n]
            except (ValueError, IndexError):
                print('Formato inválido. Use "last N" ou "l N" onde N é um número.')
                continue
        
        # Tentar interpretar como números separados por vírgula
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            selected = []
            for idx in indices:
                if 1 <= idx <= len(available_years):
                    selected.append(available_years[idx - 1])
                else:
                    print(f'Aviso: Índice {idx} fora do intervalo válido (1-{len(available_years)})')
            if selected:
                return selected
            else:
                print('Nenhum ano válido selecionado.')
                continue
        except ValueError:
            print('Entrada inválida. Tente novamente.')
            continue


def handle_existing_file(filepath, global_skip_all=False, global_overwrite_all=False):
    """
    Lida com arquivos existentes
    Retorna (action, updated_global_skip, updated_global_overwrite)
    action pode ser 'skip' ou 'overwrite'
    """
    if not os.path.exists(filepath):
        return ('overwrite', global_skip_all, global_overwrite_all)
    
    if global_skip_all:
        return ('skip', global_skip_all, global_overwrite_all)
    
    if global_overwrite_all:
        return ('overwrite', global_skip_all, global_overwrite_all)
    
    # Solicitar ao usuário
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    size_mb = file_size / (1024 * 1024)
    
    while True:
        choice = input(f'\nArquivo já existe: {filename} ({size_mb:.2f} MB)\n'
                     f'  [s] Pular este arquivo\n'
                     f'  [o] Sobrescrever este arquivo\n'
                     f'  [sa] Pular todos os arquivos existentes\n'
                     f'  [oa] Sobrescrever todos os arquivos existentes\n'
                     f'Escolha: ').strip().lower()
        
        if choice == 's':
            return ('skip', False, False)
        elif choice == 'o':
            return ('overwrite', False, False)
        elif choice == 'sa':
            return ('skip', True, False)
        elif choice == 'oa':
            return ('overwrite', False, True)
        else:
            print('Opção inválida. Use s, o, sa ou oa.')


def main():
    """Função principal"""
    print(time.asctime(), f'Início de {sys.argv[0]}:')
    print('='*60)
    
    # Configurar diretórios
    setup_directories()
    
    # Obter anos disponíveis
    available_years = get_election_years()
    
    if not available_years:
        print('Nenhum ano de eleição encontrado.')
        sys.exit(1)
    
    # Solicitar seleção de anos
    selected_years = prompt_year_selection(available_years)
    
    if not selected_years:
        print('Nenhum ano selecionado.')
        sys.exit(0)
    
    print(f'\nProcessando {len(selected_years)} ano(s) de eleição...')
    
    # Contadores
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    failed_downloads = []
    
    # Flags globais para tratamento de arquivos existentes
    global_skip_all = False
    global_overwrite_all = False
    
    # Processar cada ano
    for year_idx, (year, year_url) in enumerate(selected_years, 1):
        print(f'\n{time.asctime()} - Processando ano {year_idx}/{len(selected_years)}: {year}')
        print('-'*60)
        
        # Criar diretório do ano
        year_dir = setup_directories(year=year)
        
        # Obter recursos do ano
        resources = get_resources_from_year(year_url, year)
        
        if not resources:
            print(f'  Nenhum recurso encontrado para {year}')
            continue
        
        # Processar cada recurso
        for res_idx, resource in enumerate(resources, 1):
            print(f'\n  Recurso {res_idx}/{len(resources)}: {resource["name"]}')
            
            # Construir caminho do arquivo
            output_path = os.path.join(year_dir, resource['name'])
            
            # Verificar se arquivo já existe
            action, global_skip_all, global_overwrite_all = handle_existing_file(
                output_path, global_skip_all, global_overwrite_all
            )
            
            if action == 'skip':
                print(f'    Pulando: {resource["name"]}')
                total_skipped += 1
                continue
            
            # Baixar arquivo com retry
            max_retries = 3
            success = False
            
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    print(f'    Tentativa {attempt}/{max_retries}...')
                    time.sleep(2 ** attempt)  # Backoff exponencial
                
                success, error_msg = download_file(resource['url'], output_path)
                
                if success:
                    total_downloaded += 1
                    print(f'    ✓ Baixado: {resource["name"]}')
                    break
                else:
                    if attempt < max_retries:
                        print(f'    ✗ Erro: {error_msg} - Tentando novamente...')
                    else:
                        print(f'    ✗ Falha após {max_retries} tentativas: {error_msg}')
                        total_failed += 1
                        failed_downloads.append({
                            'year': year,
                            'filename': resource['name'],
                            'url': resource['url'],
                            'error': error_msg
                        })
    
    # Resumo final
    print('\n' + '='*60)
    print('RESUMO DO DOWNLOAD')
    print('='*60)
    print(f'Total baixado: {total_downloaded}')
    print(f'Total pulado: {total_skipped}')
    print(f'Total falhou: {total_failed}')
    print('='*60)
    
    # Salvar lista de falhas
    if failed_downloads:
        failed_file = os.path.join(PASTA_BASE, 'failed_downloads.txt')
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write('Falhas no download:\n')
            f.write('='*60 + '\n')
            for item in failed_downloads:
                f.write(f"Ano: {item['year']}\n")
                f.write(f"Arquivo: {item['filename']}\n")
                f.write(f"URL: {item['url']}\n")
                f.write(f"Erro: {item['error']}\n")
                f.write('-'*60 + '\n')
        print(f'\nLista de falhas salva em: {failed_file}')
    
    print(f'\n{time.asctime()} - Finalizou {sys.argv[0]}!!!')
    
    if __name__ == '__main__':
        input('\nPressione Enter para sair...')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nInterrompido pelo usuário.')
        sys.exit(0)
    except Exception as e:
        print(f'\nErro inesperado: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

