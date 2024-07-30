# -*- coding: utf-8 -*-
from utils import util
from face_age import r_age, duratation_age
from face_sex import r_sex, duratation_sex
from face_score import r_face_score, duratation_face_score
from face_expression import r_expression, duratation_expression


def write_txt(a, b, c, d):
    util.write_to_file('temp_data_dir/iflytek.log', f'----------------------------age年龄------------------------------\n')
    util.write_to_file('temp_data_dir/iflytek.log', f'{a}', need_json=False)
    util.write_to_file('temp_data_dir/iflytek.log',
                       f'\n--------------------age耗时：{duratation_age}秒----------------------\n')

    util.write_to_file('temp_data_dir/iflytek.log', f'----------------------------sex性别------------------------------\n')
    util.write_to_file('temp_data_dir/iflytek.log', f'{b}\n', need_json=True)
    util.write_to_file('temp_data_dir/iflytek.log',
                       f'\n--------------------age耗时：{duratation_sex}秒----------------------\n')

    util.write_to_file('temp_data_dir/iflytek.log', f'----------------------------face_score颜值------------------------------\n')
    util.write_to_file('temp_data_dir/iflytek.log', f'{c}\n', need_json=True)
    util.write_to_file('temp_data_dir/iflytek.log',
                       f'\n--------------------face_score耗时：{duratation_face_score}秒----------------------\n')

    util.write_to_file('temp_data_dir/iflytek.log', f'----------------------------expression表情------------------------------\n')
    util.write_to_file('temp_data_dir/iflytek.log', f'{d}\n', need_json=True)
    util.write_to_file('temp_data_dir/iflytek.log',
                       f'\n--------------------expression耗时：{duratation_expression}秒----------------------\n')
    print(f'--------------------all success----------------------\n')


write_txt(r_age, r_sex, r_face_score, r_expression)
