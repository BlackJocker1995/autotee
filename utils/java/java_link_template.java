package com.example.project;

import java.io.*;
import java.util.Arrays;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
 
public class SensitiveFun {
    private static final Gson gson = new Gson();
 
    public static {{ return_type }} {{ function_name }}({{ signature_params }}) {
        try {
            String[] cmd = {"cargo", "run", "--bin", "rust", "--manifest-path", "rust/Cargo.toml", "--quiet"};
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(new File("."));
            pb.redirectErrorStream(true);
            Process process = pb.start();
            JsonObject request = new JsonObject();
            
            request.addProperty("function_name", "{{ function_name }}");

            JsonObject params = new JsonObject();
            {% for param_name, param_type in arguments.items() %}
            {% if param_type == 'byte[]' %}
            JsonArray {{ param_name }}Array = new JsonArray();
            for (byte b : {{ param_name }}) {
                {{ param_name }}Array.add(b & 0xFF);
            }
            params.add("{{ param_name }}", {{ param_name }}Array);
            {% elif param_type in ['int', 'Integer', 'long', 'Long', 'double', 'Double', 'float', 'Float', 'boolean', 'Boolean', 'String'] %}
            params.addProperty("{{ param_name }}", {{ param_name }});
            {% else %}
            params.add("{{ param_name }}", gson.toJsonTree({{ param_name }}));
            {% endif %}
            {% endfor %}
            request.add("params", params);  

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
            
            return response.get("data").{{ getter_method }}();
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to call Rust {{ function_name }} function", e);
        }
    }
}