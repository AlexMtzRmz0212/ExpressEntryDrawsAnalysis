<details open>
<summary><code>main()</code></summary>

- <details open>
  <summary><code>manager.update_data()</code></summary>

  - <details open>
    <summary><code>fetcher.fetch_json()</code></summary>
    
    - `response = requests.get()`
    - `response.raise_for_status()`
    - `return response.json()`
    
    </details>
  
  - <details open>
    <summary><code>processor.process_data()</code></summary>
    
    - `return df[selected_columns].sort_values('drawDate', ascending=False).reset_index(drop=True)`
    
    </details>

  
  - <details open>
    <summary><code>tracker.get_existing_data()</code></summary>
    
    - `if DRAWS_JSON.exists()`
      - `data = json.load()`
    
    </details>
    
  - Add Metadata
  - if not existing or existing less than new
    - <mark>Write JSON file</mark>


  </details>

- <details open>
  <summary><code>manager.analyzer.analyze(data)</code></summary>
  
  - <details><summary><code>clean_df()</code></summary></details>
  - <details><summary><code>get_date_range()</code></summary></details>
  - <details><summary><code>calculate_size_stats()</code></summary></details>
  - <details><summary><code>calculate_score_stats()</code></summary></details>
  - <details><summary><code>analyze_draw_times()</code></summary></details>
  - <details><summary><code>_save_analysis()</code></summary></details>
  
  </details>

</details>