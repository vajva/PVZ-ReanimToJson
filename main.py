# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import re
import json

from bs4 import BeautifulSoup



def filter_use_data(content):
    pattern = re.compile(r'<name>([\w ]+)</name>')
    l = pattern.split(content)[1:]
    i = 0
    q = {}
    result = []
    for s in l:
        if i % 2 == 0:
            q = {"name": s}
        else:
            q["content"] = s
            result.append(q)
        i = i + 1
    return result


def replenish_omit_data(image_xml_data):
    content = image_xml_data['content']
    soup = BeautifulSoup(content, 'html.parser')
    frame_list = soup.find_all('t')
    pre_frame_data = None
    use_pre = False
    image = None
    final_data = []
    index = 0
    is_none = False
    for frame in frame_list:
        json_data = {}
        if pre_frame_data is not None:
            use_pre = True
        for arg in frame.children:
            arg_name = arg.name
            arg_data = arg.string
            if arg_name == "i":
                arg_data = arg_data.replace("IMAGE_REANIM_", "").lower()
                image = arg_data
            json_data[arg_name] = arg_data
            if arg_name == "f":
                if arg_data == "-1":
                    is_none = True
                    # use_pre = False
                else:
                    is_none = False
        if image is None:
            is_none = True
        # else:
        #     if "gatlingpea_blink" in image:
        #         print(pre_frame_data)
        replenish_args_default_map = {'sx': 1, 'sy': 1, 'kx': 0, 'ky': 0, 'x': 0, 'y': 0, "i": None}
        index = index + 1
        if not is_none and pre_frame_data is not None and use_pre:
            for replenish_arg in replenish_args_default_map:
                if replenish_arg not in json_data and replenish_arg in pre_frame_data:
                    json_data[replenish_arg] = pre_frame_data[replenish_arg]

        if not is_none:
            for replenish_arg in replenish_args_default_map:
                if replenish_arg not in json_data:
                    json_data[replenish_arg] = replenish_args_default_map[replenish_arg]
            pre_frame_data = json_data
            if image is not None:
                json_data["i"] = image
        # else:
        #     pre_frame_data = None

        final_data.append(json_data)
    image_xml_data['content'] = final_data


def getFrame(num, l):
    result = []
    for i in l:
        content = i["content"][num]
        q = {}
        for k in content:
            if content[k] is not None:
                q[k] = content[k]
        if len(q) != 0:
            result.append(q)
    return result


def remove_action_data(image_xml_data_list):
    action_map = {}
    need_remove_map = {}
    for image_data in image_xml_data_list:
        content = image_data['content']
        empty = True
        filter_name = image_data['name'].replace("anim_", "")
        for json_data in content:
            if "i" in json_data:
                empty = False
        need_remove_map[filter_name] = empty
        if ("anim_" in image_data['name']) or image_data['name'] == "Sun1":
            action_map[filter_name] = {}
    filter_data_list = []
    for image_data in image_xml_data_list:
        filter_name = image_data['name'].replace("anim_", "")
        if not need_remove_map[filter_name]:
            filter_data_list.append(image_data)
        index = 0
        content = image_data['content']
        if filter_name not in action_map:
            continue
        begin = None
        over = None
        if "f" not in content[0] or content[0]["f"] == 0:
            begin = 0
        # print(content)
        # print(len(content))
        for c in content:
            if begin is not None and over is not None:
                break
            if begin is None and len(c) > 0:
                if not ("f" in c and c['f'] == "-1"):
                    begin = index
            if over is None and begin is not None and len(c) > 0:
                if "f" in c and c['f'] == "-1":
                    over = index - 1
            index = index + 1

        if over is None:
            over = index - 1

        action_map[filter_name]['begin'] = begin
        action_map[filter_name]['over'] = over
    image_xml_data_list.clear()
    for filter_data in filter_data_list:
        image_xml_data_list.append(filter_data)
    return action_map


def c_build(begin, over, all_image_data_list):
    result = []
    i = begin
    while i <= over:
        child_result = []
        for image_data_list in all_image_data_list:
            data = image_data_list['content'][i]
            if "f" in data:
                data.pop("f")
            if len(data) > 0:
                child_result.append(image_data_list['content'][i])
        i = i + 1
        result.append(child_result)
    return result


def speed_build(begin, over, speed_data):
    result = []
    i = begin

    while i <= over:
        result.append(speed_data[i])
        i = i + 1
    return result


def get_speed_data(original_data_list):
    result = []
    content = None
    now_x = None
    for data in original_data_list:
        if data['name'] == '_ground':
            content = data['content']
    if content is None:
        return result
    for frame in content:
        speed = 0
        if "f" in frame:
            if frame["f"] == "0":
                speed = 0
                now_x = float(frame['x'])
            else:
                speed = 0
        elif "x" not in frame:
            speed = 0
        else:
            x = float(frame['x'])
            if (now_x == None):
                now_x = x
            speed = '%.4f' % (x - now_x)
            now_x = x
        result.append(float(speed))

    return result


def build(name):
    with open("zombie" + "/" + name + '.reanim') as file_obj:
        content = file_obj.read()
    original_data_list = filter_use_data(content)

    for original_data in original_data_list:
        replenish_omit_data(original_data)
    speed_data = get_speed_data(original_data_list)
    action_map = remove_action_data(original_data_list)

    result = {}
    images = set()

    for action in action_map:
        data = action_map[action]
        result[action] = {}
        action_list = c_build(data['begin'], data['over'], original_data_list)
        for w in action_list:
            for e in w:
                images.add(e['i'])

        result[action]['actionList'] = action_list
        if len(speed_data) > 0:
            speed_list = speed_build(data['begin'], data['over'], speed_data)
            speed_list = speed_list[1:] + [0]
            result[action]['speedList'] = speed_list
    l=[]
    for image in images:
        l.append(image)
    with open("C:\\Users\\Administrator\\Desktop\\json\\" + name + ".json", "w", encoding='utf-8') as f:
        f.write(json.dumps(result))
        f.close()

if __name__ == '__main__':
    l = ['LadderZombie']
    for i in l:
        build(i)
