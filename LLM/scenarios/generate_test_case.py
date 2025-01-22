from LLM.action import Scenario

class BaseTestCaseScenario(Scenario):
    test_case_example = ""

    @classmethod
    def get_system_prompt(cls, language: str, prompt_type: str) -> str:
        if prompt_type == "one_case":
            return f"""
                   You are a {language} programmer. 
                   I will provide you with a code snippet. 
                   First, make it static. 
                   Then, merge a main function to call this function in order to create a complete executable program. 
                   Please remember to import the necessary dependencies. 
                   If a key is required, please make an attempt to provide one in the corresponding format.
                   And if there needs any token, seed, init_str, use "test".

                   Only return the code. 
                   For example:
                   {cls.test_case_example}
                   """
        elif prompt_type == "mul_case":
            return f"""
                   As a {language} programmer, 
                   I will provide you with a code snippet. 
                   First, make it static. 
                   Then, write a main function with different test input to call this function to cover as many line coverage of the code snippet as possible.
                   Make sure the code can be a complete executable program.
                   Please remember to import the necessary dependencies. 
                   If a key is required, please make an attempt to provide one in the corresponding format.
                   And if there needs any token, seed, init_str, use "test".
                   Only return the code. 
                   For example:
                   {cls.test_case_example}
                   """
        else:
            raise ValueError("Invalid prompt type")

    @classmethod
    def query_prompt(cls, code: str) -> str:
        return f"The function code is: {code}"

    @staticmethod
    def class_generator(language: str, scenario_type: str):
        class_dict = {
            "one_case": {
                "java": GenerateOneTestCaseScenarioJava,
                "python": GenerateOneTestCaseScenarioPython,
                "rust": GenerateOneTestCaseScenarioRust
            },
            "mul_case": {
                "java": GenerateMulTestCaseScenarioJava,
                "python": GenerateMulTestCaseScenarioPython
            }
        }
        return class_dict[scenario_type][language]

class GenerateOneTestCaseScenario(BaseTestCaseScenario):
    @classmethod
    def one_case_system_prompt(cls, language: str) -> str:
        return cls.get_system_prompt(language, "one_case")

class GenerateMulTestCaseScenario(BaseTestCaseScenario):
    @classmethod
    def mul_case_system_prompt(cls, language: str) -> str:
        return cls.get_system_prompt(language, "mul_case")

class GenerateOneTestCaseScenarioJava(GenerateOneTestCaseScenario):
    test_case_example = """
    ```
    public SecretKey generateSecretKey() {
        try {
            KeyGenerator generator = KeyGenerator.getInstance("AES");
            generator.init(Constants.AES_KEY_LEN_BITS);
            return generator.generateKey();
        } catch (NoSuchAlgorithmException e) {
            return null;
        }
    }
    ```

    can be 
    ```
    import javax.crypto.KeyGenerator;
    import javax.crypto.SecretKey;

    public class Test {
        public static void main(String[] args) {
            SecretKey secretKey = generateSecretKey();
            if (secretKey != null) {
                System.out.println("Secret key generated successfully.");
            } else {
                System.out.println("Failed to generate secret key.");
            }
        }

        public static SecretKey generateSecretKey() {
            try {
                KeyGenerator generator = KeyGenerator.getInstance("AES");
                generator.init(128); 
                return generator.generateKey();
            } catch (Exception e) {
                e.printStackTrace();
                return null;
            }
        }
    }
    ```
    """

class GenerateOneTestCaseScenarioPython(GenerateOneTestCaseScenario):
    test_case_example = """
    ```
    def aes_cfb(key, iv, data, decrypt=True, segment_size=128):
        cipher = AES.new(key, AES.MODE_CFB, IV=iv, segment_size=segment_size)
        if decrypt:
            plaintext = cipher.decrypt(data)
            return plaintext
        else:
            ciphertext = cipher.encrypt(data)
            return ciphertext
    ```

    can be 
    ```
    from Crypto.Cipher import AES
    import base64

    def aes_cfb(key, iv, data, decrypt=True, segment_size=128):
        cipher = AES.new(key, AES.MODE_CFB, IV=iv, segment_size=segment_size)
        if decrypt:
            plaintext = cipher.decrypt(data)
            return plaintext
        else:
            ciphertext = cipher.encrypt(data)
            return ciphertext

    if __name__ == "__main__":
        key = b'testkeytestkey12'  # Key must be 16, 24, or 32 bytes long
        iv = b'testiv1234567890'  # IV must be 16 bytes long
        data = b'test'
        
        # Encrypting the data
        encrypted_data = aes_cfb(key, iv, data, decrypt=False)
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        print(f"Encrypted Data: {encrypted_data_base64}")

        # Decrypting the data
        encrypted_data_bytes = base64.b64decode(encrypted_data_base64)
        decrypted_data = aes_cfb(key, iv, encrypted_data_bytes, decrypt=True)
        print(f"Decrypted Data: {decrypted_data}")
    ```
    """

class GenerateOneTestCaseScenarioRust(GenerateOneTestCaseScenario):
    test_case_example = """
    ```
    public SecretKey generateSecretKey() {
        try {
            KeyGenerator generator = KeyGenerator.getInstance("AES");
            generator.init(Constants.AES_KEY_LEN_BITS);
            return generator.generateKey();
        } catch (NoSuchAlgorithmException e) {
            return null;
        }
    }
    ```

    can be 
    ```
    import javax.crypto.KeyGenerator;
    import javax.crypto.SecretKey;

    public class Test {
        public static void main(String[] args) {
            SecretKey secretKey = generateSecretKey();
            if (secretKey != null) {
                System.out.println("Secret key generated successfully.");
            } else {
                System.out.println("Failed to generate secret key.");
            }
        }

        public static SecretKey generateSecretKey() {
            try {
                KeyGenerator generator = KeyGenerator.getInstance("AES");
                generator.init(128); 
                return generator.generateKey();
            } catch (Exception e) {
                e.printStackTrace();
                return null;
            }
        }
    }
    ```
    """

class GenerateMulTestCaseScenarioJava(GenerateMulTestCaseScenario):
    test_case_example = """
    ```
    public SecretKey generateSecretKey() {
        try {
            KeyGenerator generator = KeyGenerator.getInstance("AES");
            generator.init(Constants.AES_KEY_LEN_BITS);
            return generator.generateKey();
        } catch (NoSuchAlgorithmException e) {
            return null;
        }
    }
    ```

    can be 
    ```
    import javax.crypto.KeyGenerator;
    import javax.crypto.SecretKey;

    public class Test {
        public static void main(String[] args) {
            // some AES_KEY_LEN_BITS make generateSecretKey return null;
            // some return generator.generateKey()
        }

        public static SecretKey generateSecretKey() {
            try {
                KeyGenerator generator = KeyGenerator.getInstance("AES");
                generator.init(128); 
                return generator.generateKey();
            } catch (Exception e) {
                e.printStackTrace();
                return null;
            }
        }
    }
    ```
    """

class GenerateMulTestCaseScenarioPython(GenerateMulTestCaseScenario):
    test_case_example = """
    ```
    def aes_cfb(key, iv, data, decrypt=True, segment_size=128):
        cipher = AES.new(key, AES.MODE_CFB, IV=iv, segment_size=segment_size)
        if decrypt:
            plaintext = cipher.decrypt(data)
            return plaintext
        else:
            ciphertext = cipher.encrypt(data)
            return ciphertext
    ```

    can be 
    ```
    from Crypto.Cipher import AES
    import base64

    def aes_cfb(key, iv, data, decrypt=True, segment_size=128):
        cipher = AES.new(key, AES.MODE_CFB, IV=iv, segment_size=segment_size)
        if decrypt:
            plaintext = cipher.decrypt(data)
            return plaintext
        else:
            ciphertext = cipher.encrypt(data)
            return ciphertext

    if __name__ == "__main__":
        key = b'testkeytestkey12'  # Key must be 16, 24, or 32 bytes long
        iv = b'testiv1234567890'  # IV must be 16 bytes long
        data = b'test'

        # Encrypting the data
        encrypted_data = aes_cfb(key, iv, data, decrypt=False)
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        print(f"Encrypted Data: {encrypted_data_base64}")

        # Decrypting the data
        encrypted_data_bytes = base64.b64decode(encrypted_data_base64)
        decrypted_data = aes_cfb(key, iv, encrypted_data_bytes, decrypt=True)
        print(f"Decrypted Data: {decrypted_data}")
    ```
    """