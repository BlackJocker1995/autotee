use std::io::{self, Read};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct Request {
    function_name: String,
    params: Params,
}

// flag ----------- start change -------------
// Param 1
#[derive(Serialize, Deserialize)]
struct Params {
    seed: i32,
    input: Vec<u8>,
}

// Param2
#[derive(Serialize, Deserialize)]
struct Response {
    status: String,
    data: Option<i32>,
    error_message: Option<String>,
}
// flag ----------- end change -------------


fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Read all input from stdin
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;
    
    // Parse JSON request
    let request: Request = serde_json::from_str(&input)
        .map_err(|e| format!("Failed to parse JSON request: {}", e))?;

    // Validate function name, 
    // TODO: need to change the name
    if request.function_name != "hash" {
        let response = Response {
            status: "error".to_string(),
            data: None,
            error_message: Some("Unsupported function".to_string()),
        };
        println!("{}", serde_json::to_string(&response)?);
        return Ok(());
    }

    // Extract parameters
    // TODO: need to change the params. I think it can use a itertive method to get each parameters.
    let seed = request.params.seed;
    let input_bytes = request.params.input;

    // Call the hash function from lib.rs
    let result = rust::hash(&input_bytes, seed);

    // Create and output JSON response
    let response = Response {
        status: "success".to_string(),
        data: Some(result),
        error_message: None,
    };
    println!("{}", serde_json::to_string(&response)?);

    Ok(())
}