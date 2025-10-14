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
            {% for param_name, param_type in arguments.items() %}
            {% if param_type == 'byte[]' %}
            if ({{ param_name }} == null) {
                {% if return_type == 'void' %}
                return;
                {% elif return_type == 'byte[]' %}
                return new byte[0];
                {% elif return_type in ['int', 'Integer', 'long', 'Long', 'short', 'Short', 'byte', 'Byte'] %}
                return 0;
                {% elif return_type in ['double', 'Double', 'float', 'Float'] %}
                return 0.0;
                {% elif return_type in ['boolean', 'Boolean'] %}
                return false;
                {% else %}
                return null;
                {% endif %}
            }
            {% endif %}
            {% endfor %}
            String[] cmd = {"cargo", "run", "--quiet"};
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(new File("rust"));
            pb.redirectErrorStream(true);
            Process process = pb.start();
            JsonObject request = new JsonObject();
            
            request.addProperty("function_name", "{{ snake_case_function_name }}");

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
            
            {% if return_type == 'byte[]' %}
            JsonArray dataArray = response.get("data").getAsJsonArray();
            byte[] data = new byte[dataArray.size()];
            for (int i = 0; i < dataArray.size(); i++) {
                data[i] = dataArray.get(i).getAsByte();
            }
            return data;
            {% else %}
            return response.get("data").{{ getter_method }}();
            {% endif %}
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to call Rust {{ function_name }} function", e);
        }
    }
}