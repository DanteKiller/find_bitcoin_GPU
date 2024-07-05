kernel_code = """
// Definindo o tamanho máximo para as chaves privadas e endereços
#define PRIVATE_KEY_SIZE 32
#define ADDRESS_SIZE 20

// Função para cópia de arrays com endereço global
void secp256k1_copy(__global uint *src, __global uint *dest) {
    for (int i = 0; i < 8; ++i) {
        dest[i] = src[i];
    }
}

// Função para realizar a operação de módulo com endereço global
int secp256k1_mod(__global uint *p, __global uint *a, __global uint *result) {
    int is_equal = 1; // Assumimos inicialmente que são iguais
    
    for (int i = 0; i < 8; ++i) {
        result[i] = a[i] % p[i];
        if (result[i] != 0) {
            is_equal = 0; // Se encontrarmos alguma diferença, não são iguais
        }
    }
    
    return is_equal;
}

// Função para subtração na curva secp256k1
void secp256k1_sub(__global uint *a, __global uint *b, __global uint *result) {
    uint borrow = 0;
    for (int i = 0; i < 8; ++i) {
        uint ai = a[i];
        uint bi = b[i];
        uint diff = ai - bi - borrow;
        if (ai >= bi + borrow) {
            borrow = 0;
        } else {
            borrow = 1;
        }
        result[i] = diff;
    }
}


void secp256k1_double(__global uint *p, __global uint *x1, __global uint *y1, __global uint *resultx, __global uint *resulty) {
    if (*y1 == 0) {
        *resultx = 0;
        *resulty = 0;
        return;
    }

    uint a = 0;
    uint lambda = (3 * (*x1) * (*x1) + a) / (2 * (*y1));
    uint nu = *y1 - lambda * (*x1);
    uint x3 = lambda * lambda - 2 * (*x1);
    uint y3 = lambda * ((*x1) - x3) - nu;

    *resultx = x3 % *p;
    *resulty = y3 % *p;
}

void secp256k1_add(__global uint *p, __global uint *x1, __global uint *y1, __global uint *x2, __global uint *y2, __global uint *resultx, __global uint *resulty) {
    if (*x1 == 0 && *y1 == 0) {
        *resultx = *x2;
        *resulty = *y2;
        return;
    }
    if (*x2 == 0 && *y2 == 0) {
        *resultx = *x1;
        *resulty = *y1;
        return;
    }

    uint a = 0;
    uint lambda, nu, x3, y3;

    if (*x1 == *x2 && *y1 != *y2) {
        *resultx = 0;
        *resulty = 0;
        return;
    }

    if (*x1 != *x2) {
        lambda = (*y2 - *y1) / (*x2 - *x1);
    } else {
        lambda = (3 * (*x1) * (*x1) + a) / (2 * (*y1));
    }
    nu = *y1 - lambda * (*x1);
    x3 = lambda * lambda - *x1 - *x2;
    y3 = lambda * ((*x1) - x3) - nu;

    *resultx = x3 % *p;
    *resulty = y3 % *p;
}

// Função para multiplicar um ponto por um escalar na curva secp256k1 com endereço global
void secp256k1_mul(__global uint *p, __global uint *scalar, __global uint *x1, __global uint *y1, __global uint *resultx, __global uint *resulty) {
    // Inicializar o ponto de resultado como o ponto no infinito (0, 0)
    *resultx = 0;
    *resulty = 0;

    // Loop através dos bits do escalar, começando do bit mais significativo
    for (int i = 31; i >= 0; --i) {
        // Dobrar o ponto atual
        secp256k1_double(p, resultx, resulty, resultx, resulty);
        
        // Verificar o bit atual do escalar
        if ((*scalar >> i) & 1) {
            // Adicionar o ponto original ao ponto dobrado
            secp256k1_add(p, resultx, resulty, x1, y1, resultx, resulty);
        }
    }
}

// Função para calcular o inverso modular de um número na curva secp256k1
void secp256k1_inv(__global uint *p, __global uint *num, __global uint *result) {
    // Utilizar o algoritmo extendido de Euclides para encontrar o inverso modular
    
    // Inicializar os coeficientes iniciais
    int a = *num;
    int b = *p;
    int x0 = 0, x1 = 1;
    int y0 = 1, y1 = 0;
    int q, r, x, y;
    
    while (b != 0) {
        q = a / b;
        r = a % b;
        
        a = b;
        b = r;
        
        x = x0 - q * x1;
        y = y0 - q * y1;
        
        x0 = x1;
        x1 = x;
        
        y0 = y1;
        y1 = y;
    }
    
    // O inverso modular de num é armazenado em result
    *result = x0;
    
    // Garantir que o resultado seja positivo
    if (*result < 0) {
        *result += *p;
    }
}

// Função para converter chave privada em chave pública
void privatekey_to_publickey(__global uint *private_key, __global uint *public_key_x, __global uint *public_key_y) {
    __global uint *Gx_local;
    __global uint *Gy_local;
    // Ponto inicial na curva secp256k1
    __global uint *Gx;
    __global uint *Gy;
    secp256k1_copy(Gx, Gx_local);
    secp256k1_copy(Gy, Gy_local);
    
    secp256k1_mul(Gx_local, private_key, Gx, Gy, public_key_x, public_key_y);
}

// Função para encontrar bitcoins dado um endereço
__kernel void find_bitcoins(__global uint *private_keys, __global uint *addresses, __global uint *results, __global uint *public_keys, uint num_keys) {
    int global_id = get_global_id(0);

    // Verificar cada chave privada
    for (int i = global_id; i < num_keys; i += get_global_size(0)) {
        __global uint *private_key = private_keys + i * PRIVATE_KEY_SIZE;
        __global uint *address = addresses + i * ADDRESS_SIZE;
        __global uint *result = results + i;
        __global uint *public_key = public_keys + i * 16;

        // Variáveis para armazenar a chave pública
        __global uint *public_key_x = public_key;
        __global uint *public_key_y = public_key + 8;

        // Calcular a chave pública correspondente à chave privada
        privatekey_to_publickey(private_key, public_key_x, public_key_y);

        // Verificar se o resultado corresponde ao endereço
        if (secp256k1_mod(public_key_x, address, public_key_x) == 0 && secp256k1_mod(public_key_y, address + 8, public_key_y) == 0) {
            *result = 1;  // Chave privada encontrada
        } else {
            *result = 0;  // Chave privada não corresponde ao endereço
        }
    }
}
"""