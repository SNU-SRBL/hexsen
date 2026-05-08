#!/bin/bash

SESSION="tribo_ros"
WORK_DIR="~/Documents/tribo-slide/ros2_ws"
CONDA_ENV="tribo"
# Using absolute path for Python path to be safe
PY_PATH="export PYTHONPATH=/home/kang/miniconda3/envs/tribo/lib/python3.10/site-packages:\$PYTHONPATH"
SETUP_CMD="source install/setup.bash"

# 1. Kill old session if it exists (to start fresh)
tmux kill-session -t $SESSION 2>/dev/null

# 2. Create New Session (This is Terminal 1)
tmux new-session -d -s $SESSION
tmux rename-window -t $SESSION:0 'Tribo_System'

# --- TERMINAL 1: Build & State Manager ---
# We create a 'build_complete' flag file so other terminals know when to start
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION:0 "rm -f /tmp/tribo_ready" C-m  # Clear old flag
# Run build, then create flag file, then run node
tmux send-keys -t $SESSION:0 "colcon build && touch /tmp/tribo_ready && $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "$PY_PATH" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo_plot state_manager" C-m

# --- TERMINAL 2: Inference ---
tmux split-window -t $SESSION:0
tmux select-layout -t $SESSION:0 tiled # Rearrange immediately
sleep 1 # Wait for pane to initialize
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
# Wait loop: Wait for /tmp/tribo_ready to exist before running
tmux send-keys -t $SESSION:0 "while [ ! -f /tmp/tribo_ready ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "$PY_PATH" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo_plot inference" C-m

# --- TERMINAL 3: App2 ---
tmux split-window -t $SESSION:0
tmux select-layout -t $SESSION:0 tiled
sleep 1
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION:0 "while [ ! -f /tmp/tribo_ready ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "$PY_PATH" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo_plot app2_old" C-m

# --- TERMINAL 4: SensorT ---
tmux split-window -t $SESSION:0
tmux select-layout -t $SESSION:0 tiled
sleep 1
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION:0 "while [ ! -f /tmp/tribo_ready ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo sensorT" C-m

# --- TERMINAL 5: Writer V2 ---
tmux split-window -t $SESSION:0
tmux select-layout -t $SESSION:0 tiled
sleep 1
tmux send-keys -t $SESSION:0 "cd $WORK_DIR" C-m
tmux send-keys -t $SESSION:0 "conda activate $CONDA_ENV" C-m
tmux send-keys -t $SESSION:0 "while [ ! -f /tmp/tribo_ready ]; do sleep 1; done; $SETUP_CMD" C-m
tmux send-keys -t $SESSION:0 "ros2 run tribo writer_v2" C-m

# Final layout adjustment
tmux select-layout -t $SESSION:0 tiled
tmux attach-session -t $SESSION