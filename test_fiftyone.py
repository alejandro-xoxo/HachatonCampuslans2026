import fiftyone as fo

dataset = fo.Dataset("test_dataset")

samples = [
    fo.Sample(filepath=f"imagen_{i}.jpg")
    for i in range(5)
]
dataset.add_samples(samples)

session = fo.launch_app(dataset)
session.wait()
