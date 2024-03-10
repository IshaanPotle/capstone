const users = [
    { username: 'user1', email: 'user1@example.com', password: 'password1'},
    { username: 'user2', email: 'user2@example.com', password: 'password2'},
    { username: 'user3', email: 'user3@example.com', password: 'password3' },
    { username: 'user4', email: 'user4@example.com', password: 'password4' },
    { username: 'user5', email: 'user5@example.com', password: 'password5' }
];

const userDropdownMenu = document.getElementById('userDropdownMenu');

users.forEach((user, index) => {
    const listItem = document.createElement('li');
    listItem.innerHTML = `<button class="dropdown-item" type="button" data-user-index="${index}">${user.username}</button>`;
    userDropdownMenu.appendChild(listItem);
});

function toggleUser(userIndex) {
    const currentUser = users[userIndex];
    alert(`You selected ${currentUser.username}`);
    window.location.href = `.html?user=${currentUser.username}`;
}

userDropdownMenu.addEventListener('click', (event) => {
    const target = event.target;
    if (target.classList.contains('dropdown-item')) {
        const userIndex = parseInt(target.getAttribute('data-user-index'));
        toggleUser(userIndex);
    }
});
