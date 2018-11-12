# P2P-chat
P2P-чат с опциональным сервером.
Основная идея проста: какую бы изощрённую схему верификации мы бы ни придумали, связать логин с пользователем даже теоретически возможно только имея сервер, которому доверяют все участники общения. Но в таком случае он становится очевидной мишенью для атак, а любая техническая неисправность сделает невозможным функционирование всей сети. К тому же, даже такая архитектура не позволяет однозначно утверждать, какой человек стоит за тем или иным пользователем чата. Так почему бы не отказаться от единого сервера, возложив задачу идентификации на собеседника? Кто лучше человека сможет определить, с кем он общается: со старым знакомым или с кем-то, кто лишь выдаёт себя за него? Именно эти две идеи (P2P-архитектура и идентификация собеседником) и лежат в основе данного проекта.

## Этапы:
1. Функции, общие для клиента и для сервера
    1. Работа в локальных/глобальных сетях
2. Серверная часть
3. Клиентская часть
    1. Взаимодействие "клиент-сервер"
    2. Взаимодействие "клиент-клиент"
    3. UI
