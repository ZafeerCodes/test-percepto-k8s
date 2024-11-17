import os
from ultralytics import YOLO
import yaml
from ultralytics.data.utils import autosplit


job_id = os.getenv("job_id")
job_name = os.getenv("job_name")
job_type = os.getenv("job_type")
epochs = int(os.getenv("epochs"))
batch_size = int(os.getenv("batch_size"))       
model_file = os.getenv("base_model")
dataset_path = os.getenv("dataset_path")
save_dir = os.getenv("save_dir")

print("model_file",model_file)

print("save dir",save_dir)

contents = os.listdir('/mnt/data')
for item in contents:
    print("item ",item)

print("job type is  ",job_type)
model_path = f"/mnt/data/yolo-models/{job_type.lower()}/{model_file}"
model = YOLO(model_path)

yaml_dir = os.path.dirname(f"/mnt/data/{dataset_path}")
images_path = os.path.join(f"/mnt/data/{dataset_path}", 'images/train')

autosplit(
        path=images_path,
        weights=(0.8, 0.2, 0.0),
        annotated_only=False,
    )

ls = os.listdir("/mnt/data/9c77fcd5-ac23-4b10-aaa5-f8f997277629/datasets/51")
print("subdir ........",ls)
yaml_file_path = f"/mnt/data/{dataset_path}/data.yaml"

data_path = f"/mnt/data/{dataset_path}"
train_txt_path = os.path.join(data_path, 'images', 'autosplit_train.txt')
val_txt_path = os.path.join(data_path, 'images', 'autosplit_val.txt')

with open(yaml_file_path, 'r') as file:
    data_yaml = yaml.safe_load(file)

data_yaml['train'] = val_txt_path
data_yaml['val'] = val_txt_path
print("data yaml is ",data_yaml['train'])

with open(yaml_file_path,"w") as file:
    yaml.dump(data_yaml,file)

if os.path.exists(yaml_dir):
    with open(yaml_file_path,"r") as file:
        content = file.read()
        print("data.yaml is ",content)
print("chekcing")
model.train(
    data=yaml_file_path,
    epochs=epochs,
    name=f"/mnt/data/{save_dir}",
    batch=batch_size,
)
print("Training started brothe")