import os
from llm_analysis import LLMAnalysis
import json
from datetime import datetime

def save_analysis_to_file(video_id: str, analysis: dict):
    """Save the analysis results to a JSON file in the output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/llm_analysis_{video_id}_{timestamp}.json"
    
    os.makedirs("output", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    return filename

def main():
    # Ensure OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set")
        print("Please set it using: export OPENAI_API_KEY='your-api-key'")
        return

    # List of video IDs to analyze
    video_ids = [
        # "NIgrGqmoeHs",
        # "Yfp0p_0-iTo",
        # "bDVpI23q8Zg",
        # "cDbYR5lE3jY",
        # "O8XIgMwILAw",
        "SqvDaSNYoCY"
    ]

    llm_analyzer = LLMAnalysis()

    for video_id in video_ids:
        print(f"\nAnalyzing video {video_id}...")
        try:
            analysis = llm_analyzer.execute(video_id)
            if analysis:
                output_file = save_analysis_to_file(video_id, analysis)
                print(f"Analysis saved to {output_file}")
                
                # Print a summary of the analysis
                print("\nSummary:")
                for category, items in analysis.items():
                    print(f"\n{category.upper()}:")
                    for item in items[:3]:  # Show first 3 items of each category
                        print(f"- {item}")
                print("...")
            else:
                print(f"No analysis results for video {video_id}")
        except Exception as e:
            print(f"Error analyzing video {video_id}: {str(e)}")

if __name__ == "__main__":
    main()
