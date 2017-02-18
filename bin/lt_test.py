from lt import encode, decode


def lt_encode(file_path):
    block_size = 1024
    with open(file_path, 'rb') as fin:
        block_list = encode.encoder(fin, blocksize=block_size)
        for block in block_list:
            print(block)


def main():
    file_path = 'google.com.png'
    lt_encode(file_path)

if __name__ == '__main__':
    main()