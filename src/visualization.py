import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_sales(data, output_path):
    """Generate a bar plot for sales data."""
    df = pd.DataFrame(data)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Quantity Sold', y='Product', hue='Product', data=df, legend=False)
    plt.title('فروش ماهانه بر اساس محصول')
    plt.xlabel('تعداد فروخته‌شده')
    plt.ylabel('محصول')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    return output_path
