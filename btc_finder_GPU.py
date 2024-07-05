import base58, time, hashlib, os, datetime, struct
import pyopencl as cl
import numpy as np
import kernel
from ranges import ranges


privatekeys = []
segundos = 0

while True:
    answer = input("Escolha uma carteira puzzle( 1 - 160): ")
    try:
        if int(answer) > 0 and int(answer) < 160:
            r = ranges[int(answer)-1]
            break
    except:
        print("Valor inválido")

tk = input("Escolha a qtde de privatekey por vez, deixe em branco para padrão que é 100000: ")
try:
    if tk == "" or int(tk) == 0:
        total_keys = 100000
    else:
        try:
            total_keys = int(tk)
        except:
            total_keys = 100000
except:
    total_keys = 100000

name = f'{datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")}_{answer}'
tk = total_keys
rmin = int(r["min"], 16)
rmax = int(r["max"], 16)

def generate_private_keys(min_int, max_int, interval=100000):
    global privatekeys
    privatekeys = []
    for i in range(min_int, max_int + 1):
        privatekeys.append(f"{i:064x}")
        if len(privatekeys) >= interval:
            break

generate_private_keys(rmin, rmax, interval=total_keys)

addresses = [line.strip() for line in open('wallets.txt', 'r').readlines()]

# Função para converter chave pública em endereço de Bitcoin
def public_key_to_address(public_key):
# def public_key_to_address(public_key_x, public_key_y):
    # Concatenate public key x and y coordinates
    # public_key = public_key_x + public_key_y

    # Take SHA-256 hash of the concatenated public key
    sha256_hash = hashlib.sha256(public_key).digest()

    # Take RIPEMD-160 hash of the SHA-256 hash
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

    # Add network byte (0x00 for mainnet) to the RIPEMD-160 hash
    extended_ripemd160_hash = b'\x00' + ripemd160_hash

    # Take SHA-256 hash of the extended RIPEMD-160 hash
    sha256_hash_again = hashlib.sha256(extended_ripemd160_hash).digest()

    # Take the first 4 bytes of the SHA-256 hash as the checksum
    checksum = sha256_hash_again[:4]

    # Concatenate the extended RIPEMD-160 hash and the checksum
    data_to_encode = extended_ripemd160_hash + checksum

    # Encode the concatenated data using Base58
    address = base58.b58encode(data_to_encode).decode('ascii')

    return address

def resultTime(tk, pkey, name):
    global segundos, start_time
    if time.time() - start_time > segundos:
        segundos += 10
        print(segundos / 1000)
        if segundos % 10 == 0:
            tempo = (time.time() - start_time)
            os.system('cls' if os.name == 'nt' else 'clear')
            print('Resumo: ')
            print('Tempo: ', tempo)
            print('Velocidade:', tk / tempo, 'haves por segundo')
            print('Chaves buscadas: ', f"{tk}")
            print('Ultima chave tentada: ', pkey)

            file_path = f'Ultima_chave_{name}.txt'  # File path to write to
            content = f"Ultima chave tentada: {pkey}"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"Error writing to file: {e}")
    return segundos

def public_key_to_private(public_keys_np):
    try:
        public_key_x_array = public_keys_np[:8]
        public_key_y_array = public_keys_np[8:]

        pkx = ''.join(str(value) for value in public_key_x_array)
        pky = ''.join(str(value) for value in public_key_y_array)
        
        # Concatena pkx e pky em uma única string
        combined_key_str = pkx + pky
        
        # Converte a string concatenada para uma string hexadecimal
        combined_key_hex = ''.join(format(int(value), 'x') for value in combined_key_str)
        
        # Converte a string hexadecimal para bytes
        private_key_bytes = bytes.fromhex(combined_key_hex)
        
        # Exibe a chave privada em bytes
        address = public_key_to_address(private_key_bytes)
        # try:
        #     with open(rf'address_encontradas_{name}.txt', 'w', encoding='utf-8') as f:
        #         f.write(address)
        # except Exception as e:
        #     print(f"Error writing to file: {e}")
    except:
        address = ""
    return address

# Código do OpenCL
kernel_code = kernel.kernel_code

# Configuração da plataforma e dispositivo OpenCL
platform = cl.get_platforms()[0]
device = platform.get_devices()[0]
context = cl.Context([device])
queue = cl.CommandQueue(context)

# Compilar o kernel
program = cl.Program(context, kernel_code).build()

start_time = time.time()

while True:
    # Converter private keys para numpy arrays
    privatekeys_np = np.array(privatekeys, dtype=object)
    # Converter addresses para numpy arrays
    addresses_np = np.array(addresses, dtype=object)

    results_np = np.zeros(len(privatekeys), dtype=np.uint32)
    public_keys_np = np.zeros((len(privatekeys), 16), dtype=np.uint32)

    # Criar buffers OpenCL
    mf = cl.mem_flags
    privatekeys_buffer = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=privatekeys_np)
    addresses_buffer = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=addresses_np)
    results_buffer = cl.Buffer(context, mf.WRITE_ONLY, results_np.nbytes)
    public_keys_buffer = cl.Buffer(context, mf.WRITE_ONLY, public_keys_np.nbytes)

    # Executar kernel
    program.find_bitcoins(queue, privatekeys_np.shape, None, privatekeys_buffer, addresses_buffer, results_buffer, public_keys_buffer, np.uint32(len(privatekeys)))

    # Ler resultados
    # cl.enqueue_copy(queue, results_np, results_buffer).wait()
    cl.enqueue_copy(queue, public_keys_np, public_keys_buffer).wait()

    # print("Results:", results_np)

    # address = [public_key_to_private(value) for value in public_keys_np]
    # address_np = np.array(address, dtype='<U34')
    # np.savetxt('address_encontradas.txt', address_np, fmt='%s', newline='\n')
    
    resultTime(tk, privatekeys[-1], name)

    if rmin <= (rmax - total_keys):
        tk += total_keys
        rmin += total_keys
    else:
        print("Finalizado")
        break
    generate_private_keys(rmin, rmax, interval=total_keys)

    