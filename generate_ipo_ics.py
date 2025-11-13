import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import pytz

def create_ics():
    cal = Calendar()
    cal.add('prodid', '-//38Korea IPO//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', '공모주 일정')
    cal.add('X-WR-TIMEZONE', 'Asia/Seoul')

    url = 'https://www.38.co.kr/html/fund/?o=k'
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')

    # 테이블 찾기
    table = soup.find('table', attrs={'border': '1'})
    if not table:
        print("테이블을 찾을 수 없습니다.")
        return

    rows = table.find_all('tr')[1:]  # 헤더 제외
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 7: 
            continue
        company = cols[0].get_text(strip=True)
        period = cols[1].get_text(strip=True)
        link = cols[0].find('a')
        if not link or 'no=' not in link['href']: 
            continue
        no = link['href'].split('no=')[1].split('&')[0]
        detail_url = f'https://www.38.co.kr/html/fund/?o=v&no={no}'
        
        # 상세 페이지
        dres = requests.get(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
        dtext = dres.text
        refund = ''
        listing = ''
        if '환불일,' in dtext:
            try:
                refund = dtext.split('환불일,')[1].split(' ')[0].replace('.', '-')
            except: 
                pass
        if '상장일,' in dtext:
            try:
                listing = dtext.split('상장일,')[1].split(' ')[0].replace('.', '-')
            except: 
                pass

        # 이벤트 추가 함수
        def add_event(title, date_str):
            if not date_str or len(date_str) < 8: 
                return
            try:
                if len(date_str) == 5:  # MM-DD만 있을 때
                    year = datetime.now().year
                    date_str = f"{year}-{date_str}"
                dt = datetime.strptime(date_str, '%Y-%m-%d').date()
                event = Event()
                event.add('summary', f'[공모주] {company} - {title}')
                event.add('dtstart', dt)
                event.add('dtend', dt)
                event.add('description', detail_url)
                cal.add_component(event)
            except Exception as e:
                print(f"이벤트 추가 실패: {title}, {e}")

        # 청약 기간 이벤트 추가
        if ' ~ ' in period:
            parts = period.replace(' ', '').split('~')
            if len(parts) == 2:
                start = parts[0].replace('.', '-')
                end = parts[1].replace('.', '-')
                add_event('청약 시작', start)
                add_event('청약 마감', end)
        add_event('환불일', refund)
        add_event('상장일', listing)

    # ics 파일 생성
    with open('ipo.ics', 'wb') as f:
        f.write(cal.to_ical())
    print("ipo.ics 생성 완료!")

create_ics()
