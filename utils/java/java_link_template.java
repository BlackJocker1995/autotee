package com.example.project;

import java.io.*;
import java.util.Arrays;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
 
public class SensitiveFun {
    private static final Gson gson = new Gson();
 
    public static int hash(byte[] input, int seed) {// need change signature to match the name and arguments.
        // Temp start...

        
        if (input == null) {
            return 0;
        }
        
        try {
            String[] cmd = {"cargo", "run", "--bin", "rust_main", "--manifest-path", "rust/Cargo.toml", "--quiet"};
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(new File("."));
            pb.redirectErrorStream(true);
            Process process = pb.start();
            JsonObject request = new JsonObject();
            
            // flag --------- start change -----------
            // TODO: Change to real function name
            request.addProperty("function_name", "hash");

            // create parameter for argument.
            JsonObject params = new JsonObject();
            params.addProperty("seed", seed);
            
            // create parameter fpr argument.
            JsonArray byteArrayNode = new JsonArray();
            for (byte b : input) {
                byteArrayNode.add(b & 0xFF); // Convert byte to unsigned int
            }
            params.add("input", byteArrayNode);
            request.add("params", params);  
            // flag --------- end change -----------

            // Send JSON request to Rust binary
            String jsonRequest = gson.toJson(request);
            OutputStream os = process.getOutputStream();
            os.write(jsonRequest.getBytes());
            os.close();
            
            // Read the JSON result from Rust binary
            InputStream is = process.getInputStream();
            StringBuilder result = new StringBuilder();
            int ch;
            while ((ch = is.read()) != -1) {
                result.append((char) ch);
            }
            is.close();
            
            // Parse the JSON response
            JsonObject response = gson.fromJson(result.toString().trim(), JsonObject.class);
            if ("error".equals(response.get("status").getAsString())) {
                throw new RuntimeException("Rust function error: " + response.get("error_message").getAsString());
            }
            
            // Wait for process to complete
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new RuntimeException("Rust process failed with exit code: " + exitCode);
            }
            
            // TODO: need to change. It may be other types.
            return response.get("data").getAsInt();
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to call Rust hash function", e);
        }
    }
}