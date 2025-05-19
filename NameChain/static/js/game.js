document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const startGameBtn = document.getElementById('start-game');
    const playAgainBtn = document.getElementById('play-again');
    const giveUpBtn = document.getElementById('give-up');
    const guessForm = document.getElementById('guess-form');
    const nameInput = document.getElementById('name-input');
    const messageDiv = document.getElementById('message');
    const currentNameEl = document.getElementById('current-name');
    const nextLetterEl = document.getElementById('next-letter');
    const nameChainEl = document.getElementById('name-chain');
    const scoreEl = document.getElementById('score');
    const finalScoreEl = document.getElementById('final-score');
    const victoryMessageEl = document.getElementById('victory-message');
    
    // Game status elements
    const firstNameEl = document.querySelector('.first-name');
    const targetNameEl = document.querySelector('.target-name');
    
    const instructionsDiv = document.getElementById('instructions');
    const gameBoardDiv = document.getElementById('game-board');
    const gameOverDiv = document.getElementById('game-over');
    
    // Game state
    let gameState = {
        currentName: '',
        targetName: '',
        chain: [],
        score: 0,
        nextLetter: '',
        attempts: 0,
        maxAttempts: 10,
        isActive: false
    };
    
    // Event Listeners
    startGameBtn.addEventListener('click', startGame);
    playAgainBtn.addEventListener('click', startGame);
    giveUpBtn.addEventListener('click', giveUp);
    guessForm.addEventListener('submit', handleGuess);
    
    // Initialize name input with autocomplete off
    nameInput.autocomplete = 'off';
    
    // Game Functions
    async function startGame() {
        try {
            const response = await fetch('/api/start-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update game state
                gameState = {
                    currentName: data.current_name,
                    targetName: data.target_name,
                    chain: data.chain,
                    score: data.score,
                    nextLetter: data.next_letter,
                    isActive: true
                };
                
                // Update UI
                updateGameUI();
                
                // Show game board, hide instructions and game over
                instructionsDiv.classList.add('d-none');
                gameBoardDiv.classList.remove('d-none');
                gameOverDiv.classList.add('d-none');
                
                // Set start name and target name
                firstNameEl.textContent = data.current_name;
                targetNameEl.textContent = data.target_name;
                
                // Display message
                showMessage(data.message, 'success');
                
                // Focus on input
                nameInput.focus();
            } else {
                showMessage('Failed to start game. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            showMessage('An error occurred. Please try again.', 'danger');
        }
    }
    
    async function handleGuess(event) {
        event.preventDefault();
        
        if (!gameState.isActive) {
            showMessage('No active game. Please start a new game.', 'warning');
            return;
        }
        
        const guess = nameInput.value.trim();
        
        if (!guess) {
            showMessage('Please enter a name.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ guess })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update game state
                gameState = {
                    currentName: data.current_name,
                    targetName: data.target_name || gameState.targetName,
                    chain: data.chain,
                    score: data.score,
                    nextLetter: data.next_letter || '',
                    isActive: !data.game_over
                };
                
                // Update UI
                updateGameUI();
                
                // Clear input
                nameInput.value = '';
                
                // Show success message
                showMessage(data.message, 'success');
                
                // Animate the newest chain item
                const chainItems = nameChainEl.querySelectorAll('.chain-item');
                if (chainItems.length > 0) {
                    const lastItem = chainItems[chainItems.length - 1];
                    lastItem.classList.add('correct-guess');
                    setTimeout(() => {
                        lastItem.classList.remove('correct-guess');
                    }, 1000);
                }
                
                // Handle game over
                if (data.game_over) {
                    handleGameOver(data.victory, data.message);
                }
            } else {
                // Show error message
                showMessage(data.message, 'danger');
                
                // Shake the input to indicate error
                nameInput.classList.add('incorrect-guess');
                setTimeout(() => {
                    nameInput.classList.remove('incorrect-guess');
                }, 500);
                
                // Handle game over
                if (data.game_over) {
                    handleGameOver(false, data.message);
                }
            }
            
            // Focus on input
            nameInput.focus();
            
        } catch (error) {
            console.error('Error submitting guess:', error);
            showMessage('An error occurred. Please try again.', 'danger');
        }
    }
    
    function updateGameUI() {
        // Update current name display
        currentNameEl.textContent = gameState.currentName;
        
        // Update next letter
        nextLetterEl.textContent = gameState.nextLetter;
        
        // Update score
        scoreEl.textContent = gameState.score;
        
        // Update chain display
        renderNameChain();
    }
    
    function renderNameChain() {
        nameChainEl.innerHTML = '';
        
        gameState.chain.forEach((name, index) => {
            const chainItem = document.createElement('div');
            chainItem.classList.add('chain-item');
            
            // Highlight the chain letter in each name (which may not be the second letter exactly)
            if (name.length > 1) {
                let chainLetterIndex = -1;
                
                // Find the first alphabetic character after the first letter
                for (let i = 1; i < name.length; i++) {
                    if (name[i].match(/[a-zA-Z]/)) {
                        chainLetterIndex = i;
                        break;
                    }
                }
                
                if (chainLetterIndex > 0) {
                    const beforeChainLetter = document.createElement('span');
                    beforeChainLetter.textContent = name.substring(0, chainLetterIndex);
                    
                    const chainLetter = document.createElement('span');
                    chainLetter.textContent = name[chainLetterIndex];
                    chainLetter.classList.add('fw-bold', 'text-warning');
                    
                    const afterChainLetter = document.createElement('span');
                    afterChainLetter.textContent = name.substring(chainLetterIndex + 1);
                    
                    chainItem.appendChild(beforeChainLetter);
                    chainItem.appendChild(chainLetter);
                    chainItem.appendChild(afterChainLetter);
                } else {
                    chainItem.textContent = name;
                }
            } else {
                chainItem.textContent = name;
            }
            
            // Add arrow between items
            if (index > 0) {
                const arrow = document.createElement('div');
                arrow.classList.add('chain-arrow');
                arrow.innerHTML = '<i class="fas fa-arrow-right"></i>';
                nameChainEl.appendChild(arrow);
            }
            
            // Highlight if this name is the target
            if (name.toLowerCase() === gameState.targetName.toLowerCase()) {
                chainItem.classList.add('target-reached');
            }
            
            nameChainEl.appendChild(chainItem);
        });
    }
    
    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `alert alert-${type}`;
        messageDiv.classList.remove('d-none');
        
        // Auto-hide success messages after 3 seconds
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.classList.add('d-none');
            }, 3000);
        }
    }
    
    // Reset game function
    async function resetGame() {
        try {
            const response = await fetch('/api/reset-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear game state
                gameState = {
                    currentName: '',
                    targetName: '',
                    chain: [],
                    score: 0,
                    nextLetter: '',
                    attempts: 0,
                    maxAttempts: 10,
                    isActive: false
                };
                
                // Hide game board, show instructions
                gameBoardDiv.classList.add('d-none');
                gameOverDiv.classList.add('d-none');
                instructionsDiv.classList.remove('d-none');
                
                // Show message
                showMessage(data.message, 'info');
            } else {
                showMessage('Failed to reset game. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error resetting game:', error);
            showMessage('An error occurred. Please try again.', 'danger');
        }
    }
    
    // Give up function
    async function giveUp() {
        if (!gameState.isActive) {
            showMessage('No active game to give up on.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/give-up', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update game state
                gameState.isActive = false;
                
                // Handle game over with the message
                handleGameOver(false, data.message);
            } else {
                showMessage('Failed to end game. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error giving up:', error);
            showMessage('An error occurred. Please try again.', 'danger');
        }
    }

    function handleGameOver(isVictory, message) {
        // Update final score
        finalScoreEl.textContent = gameState.score;
        
        // Update victory message
        victoryMessageEl.textContent = message || (isVictory ? 
            `Congratulations! You reached the target ${gameState.targetName}!` : 
            "Game over! Better luck next time!");
        
        // Hide game board, show game over
        setTimeout(() => {
            gameBoardDiv.classList.add('d-none');
            gameOverDiv.classList.remove('d-none');
        }, 1500);
        
        // Set game inactive
        gameState.isActive = false;
    }
});
