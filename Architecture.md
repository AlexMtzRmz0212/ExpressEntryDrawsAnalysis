<details open>
<summary><code>main()</code></summary>

- <details open>
  <summary><code>manager.JUST_UPDATE()</code></summary>
  
  - <details open>
    <summary><code>manager.update_data()</code></summary>
    
    - <details open>
      <summary><code>fetcher.fetch_json()</code> ---> <code>self.raw_dict</code></summary>
      
      - `response = requests.get(URL)`
      - `response.raise_for_status()`
      - `return response.json()`
      
      </details>
    
    - <details open>
      <summary><code>processor.process_data()</code> ---> <code>self.processed_df</code></summary>
      
      - `return df[selected_columns].sort_values('drawDate', ascending=False).reset_index(drop=True)`
      
      </details>

    - <details open>
      <summary><code>tracker.get_existing_data()</code></summary>
      
      - `if DRAWS_JSON.exists()`
        - `data = json.load()`
      
      </details>

    - <details open>
      <summary><mark>Add Metadata</mark></summary>
      </details>

    - <details open> 
      <summary>if not existing | existing less than new</summary>

      - <details> 
        <summary><mark>Write JSON and CSV file</mark></summary>

        - <details>
          <summary>
          <code>self.save_file(data, self.config.DRAWS_JSON, 'json')</code><br>
          <code>self.save_file(new_df, self.config.PROCESSED, 'csv')</code>
          </summary>
          
          - <details>
            <summary><code>save_file(data, filepath, format)</code></summary>
            
            ```
            if format == auto
              if filepath.suffix.lower() == 
                json
                  if DataFrame | Series
                    data.to_dict()
                  json.dump(data)
                csv
                  if DataFrame
                    data.to_csv()
                  if dict | list
                    pd.DataFrame(data).to_csv()
                pkl | pickle
                  pickle.dump(data)
                parquet 
                  if DataFrame
                    data.to_parquet()
                  if dict | list
                    pd.DataFrame(data).to_parquet()               
            ```
            </details>
          </details>
        </details>
      </details>
    </details>
  </details>

- <details open>
  <summary><code>manager.analyzer.UPDATE_AND_ANALYZE()</code></summary>
  
  - <summary><code>manager.analyzer.update_data()</code></summary>

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

</details>