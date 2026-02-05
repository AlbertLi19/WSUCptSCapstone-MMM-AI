import pandas as pd
import os

# Folder containing your CSV files
folder_path = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/63020B_TP/'
output_file = 'combined_data_63020B_TP.csv'

# Initialize an empty DataFrame to store combined data
combined_df = pd.DataFrame(columns=['Size', 'Aspect_Ratio', 'Orientation', 'Distance'])

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        
        # Read the current CSV file
        df = pd.read_csv(file_path)
        
        # Only keep relevant columns, add missing columns with NaN if necessary
        for col in ['Size', 'Aspect_Ratio', 'Orientation', 'Distance']:
            if col not in df.columns:
                df[col] = pd.NA  # Add missing column with NaN values
        
        # Select and reorder the columns in the required order
        df = df[['Size', 'Aspect_Ratio', 'Orientation', 'Distance']]
        
        # Append to the combined DataFrame
        combined_df = pd.concat([combined_df, df], ignore_index=True)

# Now process combined_df to merge rows with complementary missing values
# Assuming the pattern is consistent (first row has one column, second row has others)

# Fill rows with missing values by combining adjacent rows
final_df = combined_df.ffill().bfill().dropna()

# Save the merged data to a new CSV file
final_df.to_csv(output_file, index=False)
