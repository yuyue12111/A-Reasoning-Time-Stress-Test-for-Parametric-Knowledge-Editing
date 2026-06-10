"""Phase 0 冒烟: EasyEdit ROME on GPT-2-XL (CPU). 在 source/EasyEdit/ 目录下运行. 预期 rewrite_acc==1.0"""
from easyeditor import BaseEditor, ROMEHyperParams

hparams = ROMEHyperParams.from_hparams('./hparams/ROME/gpt2-xl')
hparams.device = 'cpu'                      # 容器无 GPU
editor = BaseEditor.from_hparams(hparams)
metrics, edited_model, _ = editor.edit(
    prompts=['The Eiffel Tower is located in'],
    ground_truth=['Paris'],
    target_new=['Rome'],
    sequential_edit=False,
)
print(metrics)
