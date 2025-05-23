from abc import ABC, abstractmethod
from collections import defaultdict
import numpy as np
from stable_baselines3.common.callbacks import CallbackList
from utils.metrics_callback import MetricsCallback
from env.cades_env import TerminationCause
from utils.seed_update_callback import SeedUpdateCallback
from stable_baselines3.common.utils import set_random_seed

class Sb3Model(ABC):

    def __init__(self, env, config, model = None):
        self.metrics_to_eval = ["avg_node_occupancy", "avg_active_node_occupancy", "message_channel_occupancy", "empty_nodes"]
        self.env = env
        self.config = config
        if model is not None:
            self.model = model
        else:
            self.model = self.initialize()
        self.warmup()


    @abstractmethod
    def initialize(self):
        pass

    @classmethod 
    def load(self):
        """
        Load a model from a specified path and return a new instance of the class.
        Must be implemented by all subclasses.
        """
        pass

    def warmup(self):
        """
        Remove the initial inference overhead of the model by running a dummy  (to get accurate inference times)
        """
        dummy_obs = self.env.observation_space.sample()
        self.model.predict(dummy_obs, deterministic=True)

    @abstractmethod
    def evaluate(self, obs=None):
        pass

    @abstractmethod
    def model_name(self):
        pass

    def set_logger(self, logger):
        self.model.set_logger(logger)

    # This method can be overridden by subclasses to implement the evaluation logic
    def _eval_callbacks(self, save_dir):
        metrics_callback = MetricsCallback(
            self.env,
            best_model_save_path=f"{save_dir}/models",
            log_path=f"{save_dir}/logs",
            eval_freq=self.config.eval_timesteps,
            deterministic=True,
            render=False,
        )
        callback_list = CallbackList([metrics_callback])
        return callback_list
    
    def set_seed(self, seed):
        set_random_seed(seed) # for model and everything else
        self.env.set_states_random_seed(seed) # for environment

    # This method can be overridden by subclasses to implement the training logic
    def train(self, save_dir):
        callback_list = self._eval_callbacks(save_dir)
        EPOCHS = self.config.epochs
        TIMESTEPS = self.config.eval_timesteps
        self.set_seed(self.config.seed)

        iters = 0
        while iters < EPOCHS:
            iters += 1
            print("Epoch #", iters)
            self.model.learn(
                total_timesteps=TIMESTEPS,
                log_interval=self.config.eval_timesteps,
                reset_num_timesteps=False,
                tb_log_name=self.model_name(),
                callback=callback_list,
            )
            # save per 1000 iterations
            if iters % EPOCHS == 0:
                self.model.save(f"{save_dir}/models/epoch_{iters}")

    def evaluate_multiple(self, num_episodes=100):
        
        all_inference_times = []
        all_episode_rewards = []
        all_episodes_len = []
        termination_cause = {str(cause): 0 for cause in TerminationCause}

        # Initialize dictionary to store lists of results for each metric
        metrics_accumulator = {metric: [] for metric in self.metrics_to_eval}
        self.set_seed(self.config.eval_seed)

        for _ in range(num_episodes):
            # Generate a new seed for the episode
            results = self.evaluate()
            all_episode_rewards.append(results["episode_reward"])
            all_episodes_len.append(results["episode_length"])
            all_inference_times.append(results["inference_time"])
            termination_cause[results["termination_cause"]] += 1

            # Accumulate each metric's results
            for metric, value in results["metrics"].items():
                    # Skip metrics if the episode was not successful
                    if results["termination_cause"] != str(TerminationCause.SUCCESS):
                        continue
                    metrics_accumulator[metric].append(value)

        # Calculate the mean for each metric
        metrics_means = {metric: float(np.mean(values)) if values else 0 for metric, values in metrics_accumulator.items()}
        # Calculate the percentage of each termination cause
        termination_cause = {cause: count / num_episodes * 100 for cause, count in termination_cause.items()}

        return {
            "mean_episode_reward": float(np.mean(all_episode_rewards)),
            "mean_episode_length": float(np.mean(all_episodes_len)) if all_episodes_len else 0,
            "mean_inference_time": float(np.mean(all_inference_times)),
            "termination_cause": termination_cause,
            "mean_metrics": metrics_means
        }