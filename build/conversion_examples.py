"""
Code conversion examples for different languages to Rust.
Contains examples of converting Java and Python code to equivalent Rust implementations.
"""

from typing import List

# Java to Rust conversion examples
JAVA_CONVERSION_EXAMPLES: List[str] = [
    """
    public SecretKey generateSecretKey() {
        try {
            KeyGenerator generator = KeyGenerator.getInstance("AES");
            generator.init(128); 
            return generator.generateKey();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    to

    use rand::Rng;

    pub fn generate_secret_key() -> Option<[u8; 16]> {
        let mut rng = rand::thread_rng();
        Some(rng.gen())
    }
    ---
    And Dependencies:
    [rand, aes]
    """,
    """
    public static String getUserHash(String email) {
        try {
            String secret = "tesadasd";
            Mac sha256_HMAC = Mac.getInstance("HmacSHA256");
            SecretKeySpec secret_key = new SecretKeySpec(secret.getBytes(), "HmacSHA256");
            sha256_HMAC.init(secret_key);

            byte[] hash = (sha256_HMAC.doFinal(email.getBytes()));
            StringBuffer result = new StringBuffer();
            for (byte b : hash) {
                result.append(String.format("%02x", b));
            }
            return result.toString();
        }
        catch (Exception e){
        }
        return "";
    }

    to

    pub fn get_user_hash(email: &str) -> String {
        use hmac::{Hmac, Mac};
        use sha2::Sha256;

        let secret = b"tesadasd";
        let mut mac = Hmac::<Sha256>::new_from_slice(secret).expect("HMAC can take key of any size");

        mac.update(email.as_bytes());
        let result = mac.finalize();
        let code_bytes = result.into_bytes();

        hex::encode(code_bytes)
    }
    ---
    And Dependencies:
    [hex, sha2, hmac]
    """,
    """
    private static SecretKeySpec initKey() {
        try {
            MessageDigest sha1 = MessageDigest.getInstance("SHA1");
            byte[] userKey_data = DEFAULT_USER_KEY.getBytes(StandardCharsets.UTF_8);
            sha1.update(userKey_data, 0, userKey_data.length);
            key = new SecretKeySpec(sha1.digest(), "test");
            return key;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    to 

    use sha1::{Sha1, Digest};

    pub fn init_key(default_user_key: &str) -> Result<SecretKeySpec, Box<dyn std::error::Error>> {
        let mut hasher = Sha1::new();
        hasher.update(default_user_key);
        let hash_bytes = hasher.finalize();
        let secret_key_spec = SecretKeySpec {
            key: hash_bytes.try_into()?,
            algorithm: String::from("Blowfish"),
        };
        Ok(secret_key_spec)
    }

    #[derive(Debug)]
    pub struct SecretKeySpec {
        pub key: [u8; 20], // SHA1 produces a 20-byte hash
        pub algorithm: String,
    }
    ---
    [dependencies]
    [sha1, base64]
    """
]

# Python to Rust conversion examples
PYTHON_CONVERSION_EXAMPLES: List[str] = [
    """
    def encode_message(message: bytes, segment_len: int) -> list:
        message += bytes(segment_len - len(message) % (segment_len))
        encoded = []
        for i in range(0, len(message), segment_len):
            block = message[i:i + segment_len]
            encoded.append(int.from_bytes(block, 'big'))
        return encoded

        to

        pub fn encode_message(message: &[u8], segment_len: usize) -> Vec<u128> {
            // Calculate padding length
            let padding = (segment_len - message.len() % segment_len) % segment_len;
            
            // Create a new buffered message with padding
            let mut buffered_message = Vec::from(message);
            buffered_message.extend(vec![0u8; padding]);

            let mut encoded = Vec::new();
            
            for chunk in buffered_message.chunks(segment_len) {
                let mut block = [0u8; 16]; // assuming segment_len will not exceed 16 for simplicity

                // Copy the chunk to block with padding at the end
                block[..chunk.len()].copy_from_slice(chunk);

                // Convert the byte array to an integer
                let number = u128::from_be_bytes(block);
                encoded.push(number);
            }

            encoded
        }
        ---
        And Dependencies:
        [rand, argon2]
    """,
    """
    def encrypt(pubkey: list, message: bytes) -> list:
        encrypted_blocks = []
        for block_int in encode_message(message, len(pubkey) // 32):
            encrypted_blocks.append([happiness(i & block_int) for i in pubkey])
        return encrypted_blocks

        to =>

        fn happiness(x: u32) -> u32 {
            // Placeholder implementation of the happiness function
            x * x
        }

        fn encode_message(message: &[u8], block_size: usize) -> Vec<u32> {
            // Placeholder implementation of the encode_message function
            message.chunks(block_size).map(|chunk| chunk.iter().fold(0, |acc, &byte| acc * 256 + byte as u32)).collect()
        }

        pub fn encrypt(pubkey: &[u32], message: &[u8]) -> Vec<Vec<u32>> {
            let block_size = pubkey.len() / 4;
            let mut encrypted_blocks = Vec::new();
            for &block_int in encode_message(message, block_size).iter() {
                let encrypted_block: Vec<u32> = pubkey.iter().map(|&i| happiness(i & block_int)).collect();
                encrypted_blocks.push(encrypted_block);
            }
            encrypted_blocks
        }
        ---
        And Dependencies:
        [rand]
    """,
    """
    def dghv_encrypt(p, N, m):
        assert 2**7 <= N < 2**8 
        q = random.getrandbits(1024)
        rmax = 2**128 / N / 4
        r = random.randint(0, rmax) 
        return p*q + N*r + m
        
        to =>
        
        pub fn dghv_encrypt(p: i64, n: u8, m: i64) -> i64 {
            assert!(2_u128.pow(7) <= n as u128 && (n as u128) < { 2_u128.pow(8) });

            let q = rand::thread_rng().gen_range(0..=u64::MAX);
            let rmax = (2_u128.pow(128) / n as u128 / 4) as u64;
            let r = rand::thread_rng().gen_range(0..=rmax);

            p * q as i64 + n as i64 * r as i64 + m
        }
        ---
        And Dependencies:
        [rand]
    """
]
