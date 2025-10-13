use std::io::{self, Read};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Serialize, Deserialize)]
struct Request {
    function_name: String,
    params: Value, // Use Value to handle dynamic parameters
}

#[derive(Serialize, Deserialize)]
struct Params {
    {% for param_name, param_type in arguments.items() %}
    {{ param_name }}: {{ param_type | java_to_rust_type }},
    {% endfor %}
}

#[derive(Serialize, Deserialize)]
struct Response {
    status: String,
    data: Option<{{ rust_return_type }}>,
    error_message: Option<String>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Read all input from stdin
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;
    
    // Parse JSON request
    let request: Request = serde_json::from_str(&input)
        .map_err(|e| format!("Failed to parse JSON request: {}", e))?;

    // Validate function name
    if request.function_name != "{{ function_name }}" {
        let response = Response {
            status: "error".to_string(),
            data: None,
            error_message: Some("Unsupported function".to_string()),
        };
        println!("{}", serde_json::to_string(&response)?);
        return Ok(());
    }

    // Extract parameters
    let params: Params = serde_json::from_value(request.params)
        .map_err(|e| format!("Failed to parse parameters: {}", e))?;

    // Call the function from lib.rs
    let result = rust::{{ function_name }}({% for param_name, param_type in arguments.items() %}params.{{ param_name }}{% if not loop.last %}, {% endif %}{% endfor %});

    // Create and output JSON response
    let response = Response {
        status: "success".to_string(),
        data: Some(result),
        error_message: None,
    };
    println!("{}", serde_json::to_string(&response)?);

    Ok(())
}