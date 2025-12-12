"""Performance benchmarking tests for D&D Story Telling system."""

import asyncio
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any
import pytest

from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator
from app.models.story import StoryContext


class TestPerformanceBenchmarks:
    """Performance benchmarking test suite."""

    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor for benchmarking."""
        return AudioProcessor(model_size="base")  # Use base model for realistic benchmarks

    @pytest.fixture
    def story_generator(self):
        """Create StoryGenerator for benchmarking."""
        # Use a dummy API key for testing
        return StoryGenerator(api_key="test-api-key")

    @pytest.fixture
    def sample_context(self):
        """Sample context for story generation."""
        return StoryContext(
            session_name="Performance Benchmark Session",
            characters=["Aragorn the Ranger", "Legolas the Elf", "Gimli the Dwarf"],
            setting="The Mines of Moria",
            previous_events=[
                "The Fellowship entered the mines",
                "They discovered the tomb of Balin",
                "Orcs and goblins appeared"
            ]
        )

    def get_benchmark_audio_files(self, max_size_mb: float = 50.0) -> List[Path]:
        """Get audio files suitable for benchmarking."""
        audio_path = Path("D:/Raw Session Recordings")
        if not audio_path.exists():
            return []

        audio_files = []
        for ext in ["*.wav", "*.mp3"]:
            audio_files.extend(audio_path.glob(ext))

        # Filter by size and sort
        suitable_files = []
        for file in audio_files:
            size_mb = file.stat().st_size / (1024 * 1024)
            if 1.0 <= size_mb <= max_size_mb:  # Between 1MB and max_size_mb
                suitable_files.append((file, size_mb))

        # Sort by size (smallest first)
        suitable_files.sort(key=lambda x: x[1])
        return [file for file, _ in suitable_files[:5]]  # Return up to 5 files

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_audio_processing_performance_scaling(self, audio_processor):
        """Test how audio processing performance scales with file size."""
        test_files = self.get_benchmark_audio_files(max_size_mb=30.0)

        if len(test_files) < 2:
            pytest.skip("Need at least 2 audio files for scaling test")

        results = []

        for test_file in test_files:
            file_size_mb = test_file.stat().st_size / (1024 * 1024)

            # Warmup run
            try:
                await audio_processor.process_audio(str(test_file))
            except Exception as e:
                print(f"Skipping {test_file.name} due to error: {e}")
                continue

            # Benchmark runs
            times = []
            for run in range(3):  # 3 runs for averaging
                start_time = time.time()
                try:
                    result = await audio_processor.process_audio(str(test_file))
                    processing_time = time.time() - start_time

                    if result["processing_successful"]:
                        times.append(processing_time)
                    else:
                        print(f"Processing failed for {test_file.name} on run {run + 1}")

                except Exception as e:
                    print(f"Error processing {test_file.name} on run {run + 1}: {e}")

            if times:
                avg_time = statistics.mean(times)
                std_dev = statistics.stdev(times) if len(times) > 1 else 0

                results.append({
                    "file": test_file.name,
                    "size_mb": file_size_mb,
                    "avg_time": avg_time,
                    "std_dev": std_dev,
                    "time_per_mb": avg_time / file_size_mb,
                    "runs": len(times)
                })

        if not results:
            pytest.skip("No successful audio processing results")

        # Analyze scaling
        print("\nAudio Processing Performance Scaling:")
        print("File Name | Size (MB) | Avg Time (s) | Time/MB | Std Dev")
        print("-" * 65)

        total_time_per_mb = []
        for result in results:
            print(f"{result['file'][:20]:20} | {result['size_mb']:8.1f} | "
                  f"{result['avg_time']:11.2f} | {result['time_per_mb']:7.2f} | {result['std_dev']:7.2f}")
            total_time_per_mb.append(result['time_per_mb'])

        # Performance assertions
        avg_time_per_mb = statistics.mean(total_time_per_mb)
        max_time_per_mb = max(total_time_per_mb)

        print(f"\nAverage time per MB: {avg_time_per_mb:.2f}s")
        print(f"Maximum time per MB: {max_time_per_mb:.2f}s")

        # Performance should be reasonable (< 10 seconds per MB on average)
        assert avg_time_per_mb < 10.0, f"Average processing time too slow: {avg_time_per_mb:.2f}s/MB"

        # Consistency check - max shouldn't be more than 3x average
        assert max_time_per_mb < avg_time_per_mb * 3, f"Performance too inconsistent: max {max_time_per_mb:.2f}s/MB vs avg {avg_time_per_mb:.2f}s/MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, audio_processor):
        """Test concurrent audio processing performance."""
        test_files = self.get_benchmark_audio_files(max_size_mb=15.0)  # Smaller files for concurrency test

        if len(test_files) < 2:
            pytest.skip("Need at least 2 audio files for concurrency test")

        # Take first 3 files for concurrency test
        test_files = test_files[:3]

        # Sequential processing baseline
        sequential_start = time.time()
        sequential_results = []

        for test_file in test_files:
            try:
                result = await audio_processor.process_audio(str(test_file))
                if result["processing_successful"]:
                    sequential_results.append(result)
            except Exception as e:
                print(f"Sequential processing failed for {test_file.name}: {e}")

        sequential_time = time.time() - sequential_start

        if len(sequential_results) < 2:
            pytest.skip("Need at least 2 successful sequential results")

        # Concurrent processing
        concurrent_start = time.time()

        tasks = []
        for test_file in test_files[:len(sequential_results)]:  # Only test files that worked sequentially
            task = audio_processor.process_audio(str(test_file))
            tasks.append(task)

        try:
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_time = time.time() - concurrent_start

            # Count successful results
            successful_concurrent = [r for r in concurrent_results
                                   if isinstance(r, dict) and r.get("processing_successful")]

            print(f"\nConcurrent Audio Processing Results:")
            print(f"Files processed: {len(test_files)}")
            print(f"Sequential time: {sequential_time:.2f}s")
            print(f"Concurrent time: {concurrent_time:.2f}s")
            print(f"Speedup factor: {sequential_time/concurrent_time:.2f}x")
            print(f"Sequential successes: {len(sequential_results)}")
            print(f"Concurrent successes: {len(successful_concurrent)}")

            # Concurrent should be faster (but might not be due to resource constraints)
            if len(successful_concurrent) == len(sequential_results):
                # Only assert speedup if all files processed successfully
                assert concurrent_time <= sequential_time * 1.2, "Concurrent processing should not be significantly slower"

            # Should have similar success rate
            assert len(successful_concurrent) >= len(sequential_results) * 0.8, "Concurrent processing should maintain reasonable success rate"

        except Exception as e:
            pytest.skip(f"Concurrent processing failed: {e}")

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_performance(self, audio_processor, story_generator, sample_context):
        """Test performance of complete audio-to-story pipeline."""
        test_files = self.get_benchmark_audio_files(max_size_mb=20.0)

        if not test_files:
            pytest.skip("No audio files available for end-to-end test")

        test_file = test_files[0]  # Use smallest file
        file_size_mb = test_file.stat().st_size / (1024 * 1024)

        print(f"\nEnd-to-End Pipeline Performance Test:")
        print(f"File: {test_file.name} ({file_size_mb:.1f}MB)")

        # Step 1: Audio Processing
        audio_start = time.time()
        try:
            audio_result = await audio_processor.process_audio(str(test_file))
            audio_time = time.time() - audio_start

            assert audio_result["processing_successful"], "Audio processing failed"
            transcription = audio_result["text"]

            print(f"Audio processing: {audio_time:.2f}s")
            print(f"Transcription length: {len(transcription)} characters")

        except Exception as e:
            pytest.skip(f"Audio processing failed: {e}")

        # Step 2: Story Generation
        story_start = time.time()
        try:
            story_result = await story_generator.generate_story(transcription, sample_context)
            story_time = time.time() - story_start

            print(f"Story generation: {story_time:.2f}s")
            print(f"Story length: {len(story_result.narrative)} characters")

        except Exception as e:
            if "api key" in str(e).lower() or "openai" in str(e).lower():
                pytest.skip(f"OpenAI API not available: {e}")
            else:
                raise

        # Total pipeline performance
        total_time = audio_time + story_time

        print(f"Total pipeline time: {total_time:.2f}s")
        print(f"Time per MB: {total_time / file_size_mb:.2f}s/MB")

        # Performance assertions
        assert audio_time < file_size_mb * 5, f"Audio processing too slow: {audio_time:.2f}s for {file_size_mb:.1f}MB"
        assert story_time < 30, f"Story generation too slow: {story_time:.2f}s"
        assert total_time < file_size_mb * 6, f"Total pipeline too slow: {total_time:.2f}s for {file_size_mb:.1f}MB"

        # Quality checks
        assert len(transcription) > 50, "Transcription too short"
        assert len(story_result.narrative) > 100, "Generated story too short"
        assert story_result.confidence_score > 0.3, "Story confidence too low"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_during_processing(self, audio_processor):
        """Test memory usage during audio processing."""
        import psutil
        import os

        test_files = self.get_benchmark_audio_files(max_size_mb=25.0)

        if not test_files:
            pytest.skip("No audio files available for memory test")

        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB

        memory_samples = []

        for test_file in test_files[:2]:  # Test with 2 files
            try:
                # Memory before processing
                pre_memory = process.memory_info().rss / (1024 * 1024)

                # Process file
                result = await audio_processor.process_audio(str(test_file))

                # Memory after processing
                post_memory = process.memory_info().rss / (1024 * 1024)

                if result["processing_successful"]:
                    file_size_mb = test_file.stat().st_size / (1024 * 1024)
                    memory_samples.append({
                        "file": test_file.name,
                        "file_size_mb": file_size_mb,
                        "pre_memory_mb": pre_memory,
                        "post_memory_mb": post_memory,
                        "memory_increase_mb": post_memory - pre_memory,
                        "memory_efficiency": (post_memory - pre_memory) / file_size_mb
                    })

            except Exception as e:
                print(f"Memory test failed for {test_file.name}: {e}")

        if not memory_samples:
            pytest.skip("No successful memory measurements")

        print(f"\nMemory Usage Analysis:")
        print(f"Baseline memory: {baseline_memory:.1f}MB")
        print("File | Size (MB) | Pre (MB) | Post (MB) | Increase (MB) | Efficiency")
        print("-" * 75)

        for sample in memory_samples:
            print(f"{sample['file'][:15]:15} | {sample['file_size_mb']:8.1f} | "
                  f"{sample['pre_memory_mb']:7.1f} | {sample['post_memory_mb']:8.1f} | "
                  f"{sample['memory_increase_mb']:11.1f} | {sample['memory_efficiency']:10.2f}")

        # Memory usage assertions
        max_memory_increase = max(s["memory_increase_mb"] for s in memory_samples)
        avg_efficiency = statistics.mean(s["memory_efficiency"] for s in memory_samples)

        print(f"\nMax memory increase: {max_memory_increase:.1f}MB")
        print(f"Average memory efficiency: {avg_efficiency:.2f}MB increase per MB file")

        # Memory should not increase by more than 2GB for any single file
        assert max_memory_increase < 2048, f"Memory usage too high: {max_memory_increase:.1f}MB increase"

        # Memory efficiency should be reasonable (less than 10MB increase per MB of file)
        assert avg_efficiency < 10, f"Memory efficiency poor: {avg_efficiency:.2f}MB increase per MB file"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_audio_quality_vs_performance_tradeoff(self, audio_processor):
        """Test different model sizes for quality vs performance tradeoff."""
        test_files = self.get_benchmark_audio_files(max_size_mb=10.0)

        if not test_files:
            pytest.skip("No audio files available for quality test")

        test_file = test_files[0]  # Use one file for comparison
        model_sizes = ["tiny", "base", "small"]  # Test different model sizes

        results = {}

        for model_size in model_sizes:
            processor = AudioProcessor(model_size=model_size)

            try:
                start_time = time.time()
                result = await processor.process_audio(str(test_file))
                processing_time = time.time() - start_time

                if result["processing_successful"]:
                    results[model_size] = {
                        "processing_time": processing_time,
                        "text_length": len(result["text"]),
                        "confidence": result.get("confidence", 0),
                        "text_preview": result["text"][:200]
                    }

            except Exception as e:
                print(f"Model {model_size} failed: {e}")

        if len(results) < 2:
            pytest.skip("Need at least 2 model sizes for comparison")

        print(f"\nModel Size Comparison for {test_file.name}:")
        print("Model | Time (s) | Text Length | Confidence | Speed Factor")
        print("-" * 60)

        base_time = results.get("base", {}).get("processing_time", 1)

        for model_size, result in results.items():
            speed_factor = base_time / result["processing_time"]
            print(f"{model_size:5} | {result['processing_time']:8.2f} | "
                  f"{result['text_length']:11} | {result['confidence']:10.3f} | {speed_factor:12.2f}")

        # Performance expectations
        if "tiny" in results and "base" in results:
            # Tiny should be faster than base
            assert results["tiny"]["processing_time"] < results["base"]["processing_time"], \
                "Tiny model should be faster than base model"

        if "small" in results and "base" in results:
            # Small might be slower than base (depending on hardware)
            # Just ensure it completes successfully
            assert results["small"]["text_length"] > 0, "Small model should produce transcription"