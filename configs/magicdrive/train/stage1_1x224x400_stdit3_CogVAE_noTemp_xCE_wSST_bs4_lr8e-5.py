# Dataset settings
num_frames = 8
bbox_mode = 'all-xyz'

data_cfg_name = "Nuscenes_map_cache_box_t_with_n2t"
img_collate_param_train = dict(
    # template added by code.
    frame_emb = "next2top",
    bbox_mode = bbox_mode,
    bbox_view_shared = False,
    keyframe_rate = 6,  # work with `bbox_drop_ratio`
    bbox_drop_ratio = 0.4,
    bbox_add_ratio = 0.1,
    bbox_add_num = 3,
    bbox_processor_type = 2,
)
dataset_cfg_overrides = (
    # key, value
    ("dataset.dataset_process_root", "/mnt/bn/occupancy3d/workspace/mzj/data/nuscenes_mmdet3d-12Hz/"),
    ("dataset.data.train.ann_file", "/mnt/bn/occupancy3d/workspace/mzj/data/nuscenes_mmdet3d-12Hz/nuscenes_interp_12Hz_infos_train_with_bid.pkl"),
    ("dataset.data.val.ann_file", "/mnt/bn/occupancy3d/workspace/mzj/data/nuscenes_mmdet3d-12Hz/nuscenes_interp_12Hz_infos_val_with_bid.pkl"),
)

# Runner
dtype = "bf16"
sp_size = 1
plugin = "zero2-seq" if sp_size > 1 else "zero2"
grad_checkpoint = False
batch_size = 1
drop_cond_ratio = 0.15

# Acceleration settings
num_workers = 8
num_bucket_build_workers = 16

# Model settings
mv_order_map = {
    0: [5, 1],
    1: [0, 2],
    2: [1, 3],
    3: [2, 4],
    4: [3, 5],
    5: [4, 0],
}
t_order_map = None

global_flash_attn = True
global_layernorm = True
global_xformers = True
micro_frame_size = None

vae_out_channels = 16

model = dict(
    type="UltraDriveSTDiT3-XL/2",
    qk_norm=True,
    pred_sigma=False,  # CHANGED
    enable_flash_attn=True and global_flash_attn,
    enable_layernorm_kernel=True and global_layernorm,
    enable_sequence_parallelism=sp_size > 1, 
    freeze_y_embedder=False,  # CHANGED
    # magicdrive
    with_temp_block=False,  # CHANGED
    use_x_control_embedder=True,
    enable_xformers = False and global_xformers,
    sequence_parallelism_temporal=False,
    use_st_cross_attn=False,
    uncond_cam_in_dim=(3, 7),
    cam_encoder_cls="magicdrivedit.models.magicdrive.embedder.CamEmbedder",
    cam_encoder_param=dict(
        input_dim=3,
        # out_dim=1152,  # no need to set this.
        num=7,
        after_proj=True,
    ),
    bbox_embedder_cls="magicdrivedit.models.magicdrive.embedder.ContinuousBBoxWithTextTempEmbedding",
    bbox_embedder_param=dict(
        n_classes=10,
        class_token_dim=1152,
        trainable_class_token=False,
        embedder_num_freq=4,
        proj_dims=[1152, 512, 512, 1152],
        mode=bbox_mode,
        minmax_normalize=False,
        use_text_encoder_init=True, 
        after_proj=True,
        # new
        num_heads=8,
        mlp_ratio=4.0,
        qk_norm=True,
        enable_flash_attn=False and global_flash_attn,
        enable_xformers=True and global_xformers,
        enable_layernorm_kernel=True and global_layernorm,
        use_scale_shift_table=True,
    ),
    map_embedder_cls="magicdrivedit.models.magicdrive.embedder.MapControlEmbedding",
    map_embedder_param=dict(
        conditioning_size=[8, 400, 400],
        block_out_channels=[16, 32, 96, 256],
        # conditioning_embedding_channels=1152,  # no need to set this.
    ),
    map_embedder_downsample_rate=4.5,  # CHANGED
    micro_frame_size=micro_frame_size,
    frame_emb_cls="magicdrivedit.models.magicdrive.embedder.CamEmbedderTemp",
    frame_emb_param=dict(
        input_dim=3,
        # out_dim=1152,  # no need to set this.
        num=4,
        after_proj=True,
        # new
        num_heads=8,
        mlp_ratio=4.0,
        qk_norm=True,
        enable_flash_attn=False and global_flash_attn,
        enable_xformers=True and global_xformers,
        enable_layernorm_kernel=True and global_layernorm,
        use_scale_shift_table=True,
    ),
    control_skip_cross_view=True,
    control_skip_temporal=True,
    # load pretrained
    # from_pretrained="./pretrained/hpcai-tech/OpenSora-STDiT-v3",
    # force_huggingface=True,  # if `from_pretrained` is a repo from hf, use this.
)
vae = dict(
    type="VideoAutoencoderKLCogVideoX",
    from_pretrained="./pretrained/CogVideoX-2b",
    subfolder="vae",
    micro_frame_size=micro_frame_size,
    micro_batch_size=1,
)

# vae = dict(
#     type="VideoAutoencoderKLHunyuan",
#     from_pretrained="./pretrained/Hunyuan",
#     subfolder="vae",
#     micro_frame_size=micro_frame_size,
#     micro_batch_size=1,
# )

text_encoder = dict(
    type="t5",
    from_pretrained= "./pretrained/t5-v1_1-xxl",
    model_max_length=300,
    shardformer=True,
)
scheduler = dict(
    type="rflow",
    use_timestep_transform=True,
    sample_method="logit-normal",
)

val = dict(
    validation_index=[1828, 4467, 5543, 20499],
    batch_size=1,
    verbose=2,
    num_sample=2,
    save_fps=12,
    seed=1024,
    scheduler = dict(
        **scheduler,
        num_sampling_steps=30,
        cfg_scale=2.0,  # base value 1, 0 is uncond
    ),
)

# Mask settings
# 25%
mask_ratios = {
    "random": 0.01,
    "intepolate": 0.002,
    "quarter_random": 0.002,
    "quarter_head": 0.002,
    "quarter_tail": 0.002,
    "quarter_head_tail": 0.002,
    "image_random": 0.0,
    "image_head": 0.22,
    "image_tail": 0.005,
    "image_head_tail": 0.005,
}

# Log settings
seed = 42
outputs = "outputs"
wandb = True
epochs = 450
log_every = 1
ckpt_every = 500 * 5

# optimization settings
load = None
grad_clip = 1.0
lr = 8e-5
ema_decay = 0.99
adam_eps = 1e-15
weight_decay = 1e-2
warmup_steps = 3000

# mzj modification
validation_before_run = False
verbose_mode = True