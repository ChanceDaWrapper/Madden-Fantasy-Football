function selectPlayer(name, team, position, points, portraitId, playerId) {
    // Add playerId as a parameter
    console.log('This button was clicked')
  
    // Update the main player info
    document.getElementById('player-name').innerText = name
    document.getElementById('player-details').innerText = team + ' - ' + position + ' | Last Season Points: ' + points
  
    var portraitUrl = 'https://madden-assets-cdn.pulse.ea.com/madden24/portraits/256/' + portraitId + '.png'
    document.getElementById('player-portrait').src = portraitUrl
  
    // Assuming getTeamColor is correctly defined and available
    const teamColor = getTeamColor(team)
    document.querySelector('.main-player-info').style.backgroundColor = teamColor
  
    // Set the draft button's data attributes
    var draftBtn = document.querySelector('.draft-btn')
    draftBtn.setAttribute('data-player-id', playerId) // Ensure this uses the correct variable
    draftBtn.setAttribute('data-player-name', name)
    draftBtn.setAttribute('data-player-position', position)
  }
  
  // This is a placeholder function. You need to replace it with your actual function that retrieves the team color.
  function getTeamColor(teamName) {
    // Example implementation. You should replace it with your own logic.
    const nflTeamColors = {
      Cardinals: '#97233F',
      Falcons: '#A71930',
      Ravens: '#241773',
      Bills: '#00338D',
      Panthers: '#0085CA',
      Bears: '#0B162A',
      Bengals: '#FB4F14',
      Browns: '#311D00',
      Cowboys: '#041E42',
      Broncos: '#FB4F14',
      Lions: '#0076B6',
      Packers: '#203731',
      Texans: '#03202F',
      Colts: '#002C5F',
      Jaguars: '#006778',
      Chiefs: '#E31837',
      Raiders: '#A5ACAF',
      Chargers: '#0080C6',
      Rams: '#002244',
      Dolphins: '#008E97',
      Vikings: '#4F2683',
      Patriots: '#002244',
      Saints: '#D3BC8D',
      Giants: '#0B2265',
      Jets: '#125740',
      Eagles: '#004C54',
      Steelers: '#FFB612',
      '49ers': '#AA0000',
      Seahawks: '#002244',
      Buccaneers: '#D50A0A',
      Titans: '#0C2340',
      Commanders: '#773141'
    }
    return nflTeamColors[teamName] || '#FFFFFF' // Default color if team not found
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.draft-btn').addEventListener('click', function (event) {
      const btn = event.target
      const playerId = btn.getAttribute('data-player-id')
      const playerName = btn.getAttribute('data-player-name')
      const playerPosition = btn.getAttribute('data-player-position')
      const playerPoints = btn.getAttribute('data-player-points')
      const portraitId = btn.getAttribute('data-portrait-id')
  
      console.log('Drafting player:', playerName)
  
      draftPlayer(playerId, playerName, playerPosition)
    })
  })
  
  function draftPlayer(playerId, playerName, playerPosition) {
    console.log('Drafting player:', playerName)
  
    // Map player positions to roster spots
    const positionMapping = {
      QB: ['QB', 'RQB'],
      HB: ['RB1', 'RB2', 'RRB'], // Handle HB as RB and map to available spots
      WR: ['WR1', 'WR2', 'RWR'], // Map WR to available spots
      TE: ['TE', 'RTE'],
    }
  
    // Find the first available spot for the player
    const availableSpots = positionMapping[playerPosition]
    let assigned = false
  
    if (Array.isArray(availableSpots)) {
      // For positions with multiple possible spots
      for (let spot of availableSpots) {
        if (!document.getElementById(spot).querySelector('.player-name').textContent) {
          document.getElementById(spot).querySelector('.player-name').textContent = playerName
          assigned = true
          break // Stop once assigned
        }
      }
    } else {
      // For positions with a single possible spot
      if (!document.getElementById(availableSpots).querySelector('.player-name').textContent) {
        document.getElementById(availableSpots).querySelector('.player-name').textContent = playerName
        assigned = true
      }
    }
  
    if (!assigned) {
      // Handle case where no spots are available (e.g., all RB spots filled)
      console.error('No available spots for', playerName, 'at position', playerPosition)
      // Optionally, show an error message to the user
    }
  
    const rosterSpotId = determineRosterSpot(playerPosition)
    if (rosterSpotId) {
      const rosterSpot = document.getElementById(rosterSpotId)
      if (rosterSpot) {
        // Update the roster spot with the player's name
        // Assuming you want to add the player's name directly to the element.
        // Adjust this line if you're using a child element to display the name.
        rosterSpot.textContent = playerName
  
        // Optionally, update the team roster in the database via AJAX or Fetch API
      }
    }
  }
  
  // Ensure this code runs after the DOM is fully loaded
  document.addEventListener('DOMContentLoaded', function () {
    // If you have multiple draft buttons, you need to attach the event listener to each
    document.querySelectorAll('.draft-btn').forEach(function (button) {
      button.addEventListener('click', function () {})
    })
  })
  
  function sortTable(n) {
    var table,
      rows,
      switching,
      i,
      x,
      y,
      shouldSwitch,
      dir,
      switchcount = 0
    tbale = document.getElementById('playersTbale')
  }