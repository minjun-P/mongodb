# 필요 모듈 임포트
import requests
import re
from bs4 import BeautifulSoup as BS
import pymongo


# 크롤링 작업 - 데이터 수집
url = 'http://www.cine21.com/rank/person/content'
page = 0
form_data = {'section': 'actor', 'period_start': '2020-06', 'gender': 'all', 'page': page}
# 여기까지 pull 방식 request 준비 완료

# 최종 결과 담을 리스트 생성
final_list = list()

# 반복문 시작
while True:
    page += 1
    form_data['page']=page
    res = requests.post(url, data=form_data)
    soup = BS(res.content, 'lxml')
    #진행상황 확인
    print(page)
    if len(soup.select('li.people_li div.name'))==0:
        # 탈출 조건 설정
        print('끝!')
        break
    else:
        actors = soup.select('li.people_li')
        for actor in actors:
            data_dict = dict()
            actor_name = actor.select_one('div.name')
            actor_link = 'http://www.cine21.com' + actor_name.a['href']
            response_actor = requests.get(actor_link)
            soup = BS(response_actor.content, 'lxml')
            infos = soup.select('div.default_info_area li')

            data_dict['배우이름'] = re.sub('\(.+\)', '', actor_name.get_text())
            data_dict['흥행지수'] = int(actor.select_one('ul.num_info strong').get_text().replace(',', ''))
            movies = actor.select('ul.mov_list li')
            movie_list = list()
            for movie in movies:
                movie_list.append(movie.get_text().strip())
            data_dict['출연영화'] = movie_list
            data_dict['순위'] = int(actor.select_one('span.grade').get_text())
            # print('<'+re.sub('\(.+\)','',actor.get_text())+'>')

            for info in infos:
                detail = re.sub('<span.+n>', '', str(info))
                detail = re.sub('<.*?>', '', detail)
                data_dict[info.span.get_text()] = detail
            #데이터 전처리 -> 홈페이지 항목 => 왜 try? 홈페이지가 없는 것도 있음
            try:
                #홈페이지 밸류를 가져와서 리스트화
                homepages = data_dict['홈페이지']
                homepages = homepages.split('\n')
                #리스트화 하면서 생긴 빈칸을 제거
                for homepage in homepages:
                    if homepage=='':
                        homepages.remove(homepage)

                # 리스트의 각 요소 빈칸 제거하기 - map 활용
                homepages = list(map(lambda x: x.strip(),homepages))
                #전처리한 데이터 집어넣기
                data_dict['홈페이지'] = homepages
            except KeyError:
                data_dict['홈페이지'] = '홈페이지 없음'
            print(data_dict)
            final_list.append(data_dict)

# mongo db 연결하기
conn = pymongo.MongoClient()
actor_db = conn.actor_db
actor_collection = actor_db.actor_collection

actor_collection.insert_many(final_list)
