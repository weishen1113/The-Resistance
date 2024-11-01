from agent import Agent
import random

class StudentAgent(Agent):
    '''An advanced agent with adaptive learning and dynamic strategy to outperform others.'''

    def __init__(self, name='StudentAgent'):
        '''Initializes the agent with suspicion tracking, game memory, and agent properties.'''
        self.name = name
        self.suspicion = {}
        self.known_spies = set()
        self.vote_history = []
        self.mission_history = []
        self.successful_missions = 0
        self.failed_missions = 0
        self.number_of_players = 0
        self.player_number = 0
        self.spy_list = []
        self.is_spy_player = False
        self.suspected_spies = []
        self.suspected_loyalists = []  

    def new_game(self, number_of_players, player_number, spy_list):
        '''Initializes the game state.'''
        self.number_of_players = number_of_players
        self.player_number = player_number
        self.spy_list = spy_list
        self.is_spy_player = self.player_number in self.spy_list
        # Suspicion tracking for other players
        self.suspicion = {player: 0.0 for player in range(self.number_of_players) if player != self.player_number}
        self.known_spies = set()
        self.vote_history = []
        self.mission_history = []
        self.successful_missions = 0
        self.failed_missions = 0

    def is_spy(self):
        '''Returns True if the agent is a spy.'''
        return self.is_spy_player

    def propose_mission(self, team_size, betrayals_required):
        '''Proposes a mission team based on suspicion levels and game context.'''
        # Spy strategy: Build trust by selecting a mix of spies and non-spies
        if self.is_spy():
            team = [self.player_number]  # Always include self as a spy
            candidates = [p for p in range(self.number_of_players) if p != self.player_number]
            random.shuffle(candidates)  # Shuffle to add unpredictability
            spies_in_team = 1  # Start with one spy (self)
            # Add spies strategically but avoid filling the team with only spies
            for player in candidates:
                if len(team) >= team_size:
                    break
                if player in self.spy_list and spies_in_team < betrayals_required:
                    team.append(player)
                    spies_in_team += 1
            # Fill the remaining slots with non-spies to reduce suspicion
            non_spies_candidates = [p for p in candidates if p not in self.spy_list]
            random.shuffle(non_spies_candidates)  # Shuffle non-spies for unpredictability
            for player in non_spies_candidates:
                if len(team) >= team_size:
                    break
                team.append(player)
            return team[:team_size]  # Return the selected team, ensuring correct size
        # Resistance strategy: Select least suspicious players and avoid known spies
        else:
            team = [self.player_number]  # Always include self in the team
            candidates = sorted(self.suspicion.keys(), key=lambda x: self.suspicion[x])  # Sort by suspicion level (low to high)
            # Prioritize players with low suspicion and those not involved in failed missions
            for player in candidates:
                if len(team) >= team_size:
                    break
                if player not in self.known_spies:
                    # Check player's involvement in failed missions
                    failed_missions = sum(1 for mission in self.mission_history if not mission['success'] and player in mission['mission'])
                    if failed_missions == 0:  # Avoid players frequently in failed missions
                        team.append(player)
            # If not enough low-suspicion players, fill remaining slots with the next least suspicious players
            if len(team) < team_size:
                remaining_candidates = [p for p in candidates if p not in team and p not in self.known_spies]
                for player in remaining_candidates:
                    if len(team) >= team_size:
                        break
                    team.append(player)
            return team[:team_size]  # Return the selected team, ensuring correct size

    def vote(self, mission, proposer, betrayals_required):
        '''Votes on the proposed mission based on suspicion, voting history, and game context.'''
        if self.is_spy():
            # Spy strategy: Early game, vote to blend in; later game, block good missions
            if any(player in self.spy_list for player in mission):
                return True  # Support missions with spies
            # Randomize some votes to avoid obvious spy behavior
            return random.random() < 0.6
        else:
            # Resistance strategy: Reject missions proposed by suspicious players or containing spies
            if proposer in self.known_spies or any(player in self.known_spies for player in mission):
                return False
            # Calculate mission risk based on the suspicion of team members
            avg_suspicion = sum(self.suspicion[player] for player in mission if player != self.player_number) / (len(mission) - 1)
            suspicion_threshold = 0.3 + (0.1 * self.failed_missions)  # Increase tolerance as game progresses
            return avg_suspicion < suspicion_threshold
    
    def vote_outcome(self, mission, proposer, votes):
        '''Updates internal state based on voting outcome.'''
        self.vote_history.append({'mission': mission, 'proposer': proposer, 'votes': votes})
        for player, vote in enumerate(votes):
            if vote and player != self.player_number and player in mission:
                self.suspicion[player] += 0.05  # Slightly increase suspicion for consistent supporters
                self.suspicion[player] = min(1.0, self.suspicion[player])
    
    def betray(self, mission, proposer, betrayals_required):    # added betray based on team spy composition
        '''Refined betrayal strategy that factors in team composition and mission stage.'''
        if not self.is_spy():
            return False
        # If near game-end and critical missions, betray strategically
        if self.failed_missions == 2 or self.successful_missions == 2:
            return True  # High priority betrayal
        # Evaluate mission composition
        spy_count_in_mission = len(set(mission) & set(self.spy_list))
        non_spy_count_in_mission = len([p for p in mission if p not in self.spy_list])
        # If the team has mostly loyalists and low suspicion spies, betray
        if non_spy_count_in_mission >= betrayals_required and spy_count_in_mission >= 1:
            return True
        # Randomize betrayal occasionally to avoid predictable patterns
        if random.random() < 0.3:
            return True
        # Default to no betrayal unless critical
        return False  

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        '''Updates internal state based on mission outcome.'''
        self.mission_history.append({'mission': mission, 'proposer': proposer, 'num_betrayals': num_betrayals, 'success': mission_success})

        if self.is_spy():
            return  # Spies do not need to track suspicion
        # Adjust suspicion based on mission outcome
        if not mission_success:
            # Mission failed: Increase suspicion on non-self players
            potential_spies = [p for p in mission if p != self.player_number and p not in self.known_spies]
            if len(potential_spies) > 0:
                increment = num_betrayals / len(potential_spies)
                for player in potential_spies:
                    self.suspicion[player] += increment
                    self.suspicion[player] = min(1.0, self.suspicion[player])
                    if self.suspicion[player] > 0.7:
                        self.known_spies.add(player)  # Confirm player as a spy
        else:
            # Mission succeeded: Decrease suspicion on non-self players
            for player in mission:
                if player != self.player_number and player not in self.known_spies:
                    self.suspicion[player] = max(0.0, self.suspicion[player] - 0.1)

    def round_outcome(self, rounds_complete, missions_failed):
        '''Updates internal counters after each round.'''
        self.successful_missions = rounds_complete - missions_failed
        self.failed_missions = missions_failed

    def game_outcome(self, spies_win, spies):
        '''Handles the game outcome, refining the loyalist strategy based on victory or defeat.'''
        for mission in self.mission_history:
            for player in mission['mission']:
                if self.is_spy():
                    # Spy strategy: Adjust suspicion based on success/failure
                    if spies_win and not mission['success'] and player in self.spy_list and player != self.player_number:
                        self.suspicion[player] = max(0.0, self.suspicion[player] - 0.3)
                    elif not spies_win and mission['success'] and player in self.spy_list and player != self.player_number:
                        self.suspicion[player] = min(1.0, self.suspicion[player] + 0.3)
                else:
                    # Loyalist strategy: Adjust suspicion based on game outcome
                    if spies_win:
                        # If spies won, increase suspicion on players involved in failed missions
                        if not mission['success']:
                            if player != self.player_number and player not in self.known_spies:
                                self.suspicion[player] = min(1.0, self.suspicion[player] + 0.3)
                    else:
                        # If Resistance won, decrease suspicion on wrongly accused players
                        if player not in spies and player != self.player_number:
                            self.suspicion[player] = max(0.0, self.suspicion[player] - 0.2)