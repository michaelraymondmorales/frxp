import sys
import time
import requests
import urllib.parse

# Base URL for your Flask API
API_URL = "http://localhost:5000"
MAPS = [
    'iterations_map',
    'normalized_iterations_map',
    'magnitudes_map',
    'initial_angles_map',
    'final_angles_map',
    'distance_map',
    'final_derivative_magnitude_map',
    'min_distance_to_trap_map',
    'min_distance_iteration_map',
    'derivative_bailout_map',
    'final_Z_real_map',
    'final_Z_imag_map',
    'final_derivative_real_map',
    'final_derivative_imag_map',
    'bailout_location_real_map',
    'bailout_location_imag_map',
    'final_Z_real_at_fixed_iteration_map',
    'final_Z_imag_at_fixed_iteration_map']

def _build_query_string(params: dict) -> str:
    """
    Builds a URL query string from a dictionary of parameters, handling URL encoding.

    Args:
        params (dict): A dictionary of key-value pairs for the query string.

    Returns:
        str: A URL query string, prefixed with a '?'.
    """
    return '?' + urllib.parse.urlencode(params)

def test_raw_maps(query_string: str) -> bool:
    """
    Tests the retrieval of all raw maps using the task ID.

    This function expects the raw maps to be available immediately, as they are
    saved automatically by the initial calculation task.

    Args:
        query_string (str): The unique query parameters of the original calculation.

    Returns:
        bool: True if all raw maps are retrieved successfully, False otherwise.
    """
    print("Testing retrieval of raw maps...")
    all_raw_ok = True
    for map_name in MAPS:
        try:
            raw_response = requests.get(f'{API_URL}/get_map{query_string}&map_name={map_name}&map_type=raw')
            raw_response.raise_for_status()
            
            content_type = raw_response.headers.get('Content-Type')
            if raw_response.status_code == 200 and content_type == 'application/octet-stream':
                if len(raw_response.content) > 100:
                    print(f" - Raw map '{map_name}' retrieved successfully.")
                else:
                    print(f" - Raw map '{map_name}' retrieved but seems empty.")
                    all_raw_ok = False
            else:
                print(f" - Failed to get raw map '{map_name}': Status code {raw_response.status_code} or wrong Content-Type: {content_type}")
                all_raw_ok = False
        except requests.exceptions.RequestException as e:
            print(f" - Failed to get raw map '{map_name}': {e}")
            all_raw_ok = False
            
    return all_raw_ok

def test_png_maps(query_string: str) -> bool:
    """
    Tests the retrieval of a few key PNG maps.

    This function correctly handles the asynchronous nature of PNG generation,
    polling the status if the map is not yet cached.

    Args:
        query_string (str): The unique query parameters of the original calculation.

    Returns:
        bool: True if all PNG maps are retrieved successfully, False otherwise.
    """
    print("Testing retrieval of PNG maps...")
    all_png_ok = True
    for map_name in MAPS:
        try:
            # Step 1: Request the PNG map
            png_response = requests.get(f'{API_URL}/get_map{query_string}&map_name={map_name}&map_type=png')
            if png_response.status_code == 200:
                # PNG is already cached, test for successful retrieval
                content_type = png_response.headers.get('Content-Type')
                if content_type == 'image/png' and len(png_response.content) > 100:
                    print(f" - PNG map '{map_name}' found in cache and retrieved successfully.")
                    continue
                else:
                    print(f" - PNG map '{map_name}' retrieved with issues (code: 200, type: {content_type}, size: {len(png_response.content)}).")
                    all_png_ok = False
                    break

            elif png_response.status_code == 202:
                print(f" - PNG map '{map_name}' not found, calculation started. Polling task status...")
                # The task is now to render the PNG
                png_task_id = png_response.json().get('task_id')
                max_retries = 60
                for _ in range(max_retries):
                    status_response = requests.get(f"{API_URL}/task_status/{png_task_id}")
                    status_response.raise_for_status()
                    task_status = status_response.json().get('state')
                    if task_status == 'SUCCESS':
                        print(f" - PNG task for '{map_name}' completed. Retrying download...")
                        # Now that it's finished, try to download again
                        final_png_response = requests.get(f'{API_URL}/get_map{query_string}&map_name={map_name}&map_type=png')
                        final_png_response.raise_for_status()
                        content_type = final_png_response.headers.get('Content-Type')
                        if content_type == 'image/png' and len(final_png_response.content) > 100:
                            print(f" - PNG map '{map_name}' retrieved successfully after calculation.")
                            break
                        else:
                            print(f" - PNG map '{map_name}' failed to download after calculation.")
                            all_png_ok = False
                            break
                    elif task_status == 'FAILURE':
                        print(f" - PNG task for '{map_name}' failed.")
                        all_png_ok = False
                        break
                    time.sleep(1)
                else:
                    print(f" - PNG task for '{map_name}' did not complete in time.")
                    all_png_ok = False
                
                if not all_png_ok:
                    break

            else:
                print(f" - Unexpected status code for PNG map '{map_name}': {png_response.status_code}")
                all_png_ok = False
                break

        except requests.exceptions.RequestException as e:
            print(f" - Failed to get PNG map '{map_name}': {e}")
            all_png_ok = False
            break
            
    return all_png_ok

def run_test_case(test_name: str, params: dict) -> bool:
    """
    Runs a single test case by queuing a fractal calculation via URL parameters and then
    attempting to retrieve all raw and a selection of PNG maps.

    Args:
        test_name (str): The name of the test case.
        params (dict): A dictionary of parameters to send to the API.

    Returns:
        bool: True if all tests for the case pass, False otherwise.
    """
    print(f"--- Running Test: {test_name} ---")
    
    # Step 1: Request the calculation and get the task ID
    print("Sending calculation request with URL parameters:")
    try:
        query_string = _build_query_string(params)
        print(query_string)
        response = requests.get(f'{API_URL}/calculate_map{query_string}')
        response.raise_for_status()
        result = response.json()
        task_id = result.get('task_id')
    except requests.exceptions.RequestException as e:
        print(f"Failed to send calculation request: {e}")
        return False
    
    if response.status_code == 200:
        print(result.get('message')) 
    elif response.status_code == 202:
        print(f"Task queued with ID: {task_id}") 
        # Step 2: Poll for initial calculation task completion
        print("Waiting for initial fractal calculation to complete...")
        max_retries = 60
        for i in range(max_retries):
            try:
                status_response = requests.get(f"{API_URL}/task_status/{task_id}")
                status_response.raise_for_status()
                task_status = status_response.json().get('state')
                if task_status == 'SUCCESS':
                    print("Initial fractal calculation completed successfully!")
                    break
                elif task_status == 'FAILURE':
                    print(f"Initial task failed. Error: {status_response.json().get('status')}")
                    return False
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Failed to poll task status: {e}")
                return False
        else:
            print("Initial task did not complete within the time limit.")
            return False
    elif not task_id:
        print("Calculation response did not contain cached status or a task ID. Check API response.")
        return False

    # Step 3: Test retrieval of raw maps (which should be ready)
    raw_test_result = test_raw_maps(query_string)

    # Step 4: Test retrieval of PNG maps (which may require on-demand calculation)
    png_test_result = test_png_maps(query_string)

    if raw_test_result and png_test_result:
        print(f"--- Test '{test_name}' passed! ---")
        return True
    else:
        print(f"--- Test '{test_name}' failed. ---")
        return False

if __name__ == "__main__":
    test_cases = [
        {"test_name": "Mandelbrot Default", "params": {}},
        {"test_name": "Mandelbrot Zoom", "params": {"x_center": -0.7436438, "y_center": 0.1318259, "x_span": 0.0001, "y_span": 0.0001, "iterations": 2048}},
        {"test_name": "Julia Set", "params": {"fractal_type": "Julia", "c_real": -0.7269, "c_imag": 0.1889}},
        {"test_name": "Power 3 Mandelbrot", "params": {"power": 3.0, "x_span": 4.0, "y_span": 4.0, "iterations": 1024}},
    ]
    
    overall_success = True
    for case in test_cases:
        if not run_test_case(case['test_name'], case['params']):
            overall_success = False
            sys.exit(1)
    
    print("\n===============================")
    if overall_success:
        print("All tests passed! The API is working correctly.")
    else:
        print("One or more tests failed. Please check the output above.")
    print("===============================")