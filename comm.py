import os, sys, base64, zlib
import logging

def initlog(file, content):
    logger = None
    logger = logging.getLogger()
    #logger = logging.getLogger('mylog')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return [logger, fh, ch]

def log_msg(file, fun_name, err_msg):
    message = '[' + fun_name + '] ' + err_msg
    logger, fh, ch = initlog(file, message)
    logger.log(logging.DEBUG, message)
    fh.flush()
    ch.flush()
    logger.removeHandler(fh)
    logger.removeHandler(ch)

def google_encode(buffer, number):
    while number:
        if number < 128:
            mod = number
            number = 0
        else:
            mod = number%128
            mod += 128
            number = number/128
        buffer.append(mod)

def update_data(buffer, data, raw=False):
    if raw is False:
        data_type = type(data).__name__
        if data_type == "bool":
            buffer.append( 1 if data is True else 0 )
        elif data_type == "int":
            google_encode(buffer,data)
        elif data_type == "str":
            google_encode(buffer,len(data))
            for c in data:
                buffer.append(ord(c))
        else:
            raise Exception( "Unhandled data type : " + data_type )
    else:
        buffer.append(data)

def generate_request(para):
    tmp = []
    pad = [10]
    result = []
    header_len = 0
    url_config =[[16], [24], [34], [42], [50],
                 [58], [66], [74], [82], [90],
                 [19, 82], [10], [20]]
    for i in range(0, 13):
        if i == 4:
            update_data(tmp, '%s:%d' % (para[4],para[2]))
        elif i == 10:
            update_data(tmp, para[i])
            header_len = len(tmp) + 1
        elif i == 11:
            update_data(tmp, len(para[i]) + 2)
        else:
            update_data(tmp, para[i])
        tmp += url_config[i]
    update_data(result, header_len)
    result = pad + result + pad + tmp
    stream = ""
    for data in result:
        stream += chr(data)
    return base64.b64encode(stream, "-_")