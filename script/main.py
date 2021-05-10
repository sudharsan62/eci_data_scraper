import requests
from bs4 import BeautifulSoup
from pprint import pprint
import csv
from pathlib import Path, PurePath
from datetime import datetime

def get_state_list():

    state_resp = (requests.get('https://results.eci.gov.in/Result2021/ConstituencywiseS22120.htm?ac=120')).text
    # print(resp)

    soup = BeautifulSoup(state_resp, 'html.parser')

    # Get the state list tag
    state_list_soup = soup.find_all('select', attrs = {'id' : 'ddlState'})
    # Gets list of all the states
    # Create a dict with state and id
    states = {}

    for item in state_list_soup[0].find_all('option'):
        # print(item.get('value'))
        # print(item.text)
        state_name = item.text
        state_id = item.get('value')

        if state_name != 'Select State':
            states.update({state_name : state_id})
    
    return states
    # print(states)

const_resp = (requests.get('https://en.wikipedia.org/wiki/List_of_constituencies_of_the_Tamil_Nadu_Legislative_Assembly')).text


soup = BeautifulSoup(const_resp, 'html.parser')

const_soup = soup.find_all('tbody')[0].find_all('tr')
# print(const_soup)
# for item in const_soup:
#     print(item.text)

state_ac = {}
i = 0
for item in (const_soup):
    # print(item)
    # print(item.find_all('td'))

    const_detail_columns = item.find_all('td')

    if len(const_detail_columns) > 3:
        # if const_detail_columns[1].find_all('a') != []:
            # print(const_detail_columns[1].find_all('a'))
            ac_id = const_detail_columns[0].text.strip()
            ac_name = const_detail_columns[1].text.strip()
            # print(ac_id)
            # print(ac_name)
            state_ac.update({ac_id : ac_name})

# if state == 'TamilNadu':
#     state_ac.pop()

# pprint.pprint(sorted((state_ac.keys())))
# pprint.pprint(sorted(state_ac, key = lambda x : int(x[0])))
# pprint.pprint((state_ac.keys()))

def dump_election_results_raw_data(state_info):

    state_name = state_info['state_name']
    state_id = state_info['state_id']
    state_const_count = state_info['state_const_count']

    # state_name = 'Tamil Nadu'
    # state_id = 'S22'
    # state_const_count = 234

    state_total_info = []
    party_dict = {}

    const_req_base_url = 'https://results.eci.gov.in/Result2021/Constituencywise'

    for ac_id in range(1, state_const_count+1):
    # for ac_id, ac_name in state_ac.items():
    # for ac_id, ac_name in {'102':''}.items():

        # if int(ac_id) > 60:
        #     break

        # ac_name = state_ac[ac_id]

        # print(f"Collecting data for Constituency {ac_id} / {len(state_ac.items())}")
        # print(f"Collecting data for Constituency {ac_id} / {state_const_count}", end = '\r')
        print(f"Collecting data for Constituency {ac_id} / {state_const_count}")

        # print(ac_id, ac_name)

        # if ac_id.strip() == '102':
        #     print('I am here')
        #     print(ac_id.strip(), ac_name)

        # if ac_id not in [56, 58]:
        #     continue

        ac_info = {}

        const_poll_url = const_req_base_url + state_id + str(ac_id) + '.htm?ac=' + str(ac_id)

        const_resp = (requests.get(const_poll_url)).text
        # print(resp)

        const_soup = BeautifulSoup(const_resp, 'html.parser')

        ac_name_soup = const_soup.find('td', attrs = {'colspan':"9", 'align':"center"})
        # print(ac_name_soup)

        ac_name = ac_name_soup.text.strip().split(state_name+'-')[1]
        # print(ac_name)

        result_table = const_soup.find('table', attrs = {'cellpadding':"5", 'cellspacing':"0", 'style':"margin: auto; width: 100%; font-family: Verdana; border: solid 1px black;font-weight:lighter", 'border':"1"})

        result_rows = result_table.find_all('tr')

        cand_name_col_no = 1
        cand_party_col_no = 2
        cand_vote_col_no = 5

        cand_list = []

        for idx_row in range(3, len(result_rows) - 1):
            # pprint.pprint(result_rows[idx_row])
            result_columns = result_rows[idx_row].find_all('td')
            
            cand_name = result_columns[cand_name_col_no].text
            cand_party = result_columns[cand_party_col_no].text
            cand_vote_count = int(result_columns[cand_vote_col_no].text)

            # print(f'{cand_name} -- {cand_party} -- {cand_vote_count}')
            cand_info = {
                'cand_name' : cand_name,
                'cand_party' : cand_party,
                'cand_vote_count' : cand_vote_count
            }

            if cand_party in party_dict.keys():
                party_total_vote = party_dict[cand_party] + cand_vote_count
                party_dict.update({cand_party : party_total_vote})
            else:
                party_dict.update({cand_party : cand_vote_count})

            cand_list.append(cand_info)
        
        # ac_info.update({'ac_id' : ac_id, 'ac_name': ac_name})
        ac_info.update({'ac_id' : ac_id, 'ac_name': ac_name})

        cand_list = sorted(cand_list, key = lambda x: int(x['cand_vote_count']), reverse = True)
        ac_info.update({'poll_details' : cand_list})
        try:
            ac_info.update({'margin' : cand_list[0]['cand_vote_count'] - cand_list[1]['cand_vote_count']})
        except Exception as err:
            ac_info.update({'margin' : 0})
            print (err)

        state_total_info.append(ac_info)

    # This empty print is to jump to next line because previous print statement was overwriting
    print()

    # print(party_dict)
    party_list = sorted(party_dict, key = party_dict.get, reverse = True)
    # print(party_list)

    curr_dir = Path(__file__).parent.absolute()
    csv_dir = curr_dir.joinpath('csv_logs')

    if not csv_dir.exists():
        csv_dir.mkdir()

    # print(csv_dir)

    new_csv_file = csv_dir.joinpath(state_name + ' - ' + str(datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")) + '.csv')

    candidate_file = csv_dir.joinpath(state_name + ' - ' + 'Candidate' + str(datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")) + '.csv')

    # print(new_csv_file)

    party_cand_list_header = party_list.copy()
    party_cand_list_header = list(map((lambda x: 'Candidate - ' + x), party_cand_list_header))

    # print(party_dict)

    party_cand_list_header_dict = {}
    for k, v in party_dict.items():
        party_cand_list_header_dict.update({'Candidate - ' + k : v})

    # print(party_cand_list_header_dict)

    field_names_cand = []
    for idx, item in enumerate(party_list):
        field_names_cand.append(item)
        field_names_cand.append(party_cand_list_header[idx])

    # print(party_cand_list_header)

    # fieldnames = ['Constituency ID', 'Constituency_Name', 'Winning_Margin'] + field_names_cand

    fieldnames = ['Constituency ID', 'Constituency_Name', 'Winning_Margin'] + party_list

    cand_fieldnames = ['Constituency ID', 'Constituency_Name', 'Winning_Margin'] + party_cand_list_header

    # print(fieldnames)

    with open(new_csv_file, 'w', newline = '') as csv_file, open(candidate_file, 'w', newline = '') as cand_file:

        writer = csv.DictWriter(csv_file, fieldnames)
        cand_writer = csv.DictWriter(cand_file, cand_fieldnames)

        writer.writeheader()
        cand_writer.writeheader()

        new_row = {}
        new_cand_row = {}

        new_row.update({'Constituency ID':''})
        new_row.update({'Constituency_Name':''})
        new_row.update({'Winning_Margin': party_dict[party_list[0]] - party_dict[party_list[1]]})

        new_cand_row.update({'Constituency ID':''})
        new_cand_row.update({'Constituency_Name':''})
        new_cand_row.update({'Winning_Margin': party_dict[party_list[0]] - party_dict[party_list[1]]})

        new_row.update(party_dict)
        new_cand_row.update(party_cand_list_header_dict)

        writer.writerow(new_row)
        cand_writer.writerow(new_cand_row)
        
        for item in state_total_info:
            new_row = {}
            new_cand_row = {}

            new_row.update({'Constituency ID':item['ac_id']})
            new_row.update({'Constituency_Name':item['ac_name']})
            new_row.update({'Winning_Margin':item['margin']})

            new_cand_row.update({'Constituency ID':item['ac_id']})
            new_cand_row.update({'Constituency_Name':item['ac_name']})
            new_cand_row.update({'Winning_Margin':item['margin']})

            for idx, party in enumerate(party_list):
                cand_party_dict = next((dict for dict in item['poll_details'] if dict['cand_party'] == party), None)

                if cand_party_dict != None:
                    new_row.update({party : cand_party_dict['cand_vote_count']})
                    new_cand_row.update({party_cand_list_header[idx] : cand_party_dict['cand_name']})

            # print(new_cand_row)
            writer.writerow(new_row)
            cand_writer.writerow(new_cand_row)



    state_total_info = sorted(state_total_info, key = lambda x : x['margin'], reverse = True)
    # pprint.pprint(state_total_info)

    with open(csv_dir.joinpath(state_name + ' - ' + str(datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")) + '_raw_log.txt'), 'w') as raw_dump:
        raw_dump.write(str(state_total_info))



if __name__ == '__main__':

    state_const_count_dict = {
        'Assam': 126, 
        'Kerala': 140, 
        'Puducherry': 30, 
        'Tamil Nadu': 234, 
        'West Bengal': 292
        }

    # state_info = {
    #     'state_name' : 'Tamil Nadu',
    #     'state_id' : 'S22',
    #     'state_const_count' : 234
    # }

    state_info_dict = get_state_list()

    # state_info = {
    #     'state_name' : 'Kerala',
    #     'state_id' : 'S11',
    #     'state_const_count' : 140
    # }

    state_info_list = []

    state_info_dict = {'West Bengal' : state_info_dict['West Bengal']}
    # print(state_info_dict)

    for k, v in state_info_dict.items():
        state_info = {}
        state_info.update({'state_name' : k})
        state_info.update({'state_id' : v})
        state_info.update({'state_const_count' : state_const_count_dict[k]})

        print(f'Crawling data for {k}')

        dump_election_results_raw_data(state_info)

        state_info_list.append(state_info)

    # pprint(state_info_list)
    print("All Good!")

        