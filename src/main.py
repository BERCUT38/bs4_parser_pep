import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from configs import configure_argument_parser, configure_logging

from outputs import control_output

from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL, EXPECTED_STATUS

from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li', attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue 
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results

def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results            

def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup,'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    print(archive_url)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')    

def pep(session):
    count_status = {
        'Accepted': 0,
        'Active': 0,
        'Deferred': 0,
        'Draft': 0,
        'Final': 0,
        'Provisional': 0,
        'Rejected': 0,
        'Superseded': 0,
        'Withdrawn': 0
    }
    response = get_response(session, PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features = 'lxml')
    main = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tr_t = main.find_all('tr')
    for tr in tqdm(tr_t[1:], desc='считаем количество PEP'):
        personal_pep_link = tr.td.find_next_sibling().find('a')['href']
        url_pep = urljoin(PEP_URL, personal_pep_link)
        response_pep =get_response(session, url_pep)
        if response_pep is None:
            return
        pep_soup = BeautifulSoup(response_pep.text, features = 'lxml')
        dl = find_tag(pep_soup, 'dl')
        dt = find_tag(dl, lambda tag: tag.name == 'dt' and 'Status' in tag.text)
        status = dt.find_next_sibling().text
        count_status[status] = count_status.get(status, 0) + 1

        try:
            pep_statuslist = EXPECTED_STATUS[tr.td.text[1:]]
        except KeyError:
            logging.info(
                f'текущий статус неизвестен'
                f'"{url_pep}".'
                f'статус в инфо о pep: {status}, '
                f'код статуса в таблице: {tr.td.text[1:]}.'
            )
            pep_statuslist = [status, ]
        if status not in pep_statuslist:        
            logging.info(f'Несовпадающие статусы у PEP: '
                         f'"{url_pep}".'
                         f'статус в инфо о pep: {status}, '
                         f'ожидаемые статусы: {pep_statuslist}.'
                         )

        results = [('Статус', 'Количество')]
        total = 0
        for key, value in count_status.items():
            results.append((key, value))
            total += value
        results.append(('Total:', total))

    return results
        


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}

def main():
    configure_logging()
    logging.info('Парсер запущен!')            
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')    
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()    
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')        

if __name__ == '__main__':
    main() 