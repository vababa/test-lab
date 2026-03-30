#!/usr/bin/env bash

links_count=$1

# очищаем директорию tests/captures
rm -rf ./tests/captures/*
# удаляем директории alure
rm -rf ./allure*

# генерируем конфиги для тестовой топологии
cd netlab
python3 render_j2.py $links_count

# запускаем тестовую топологию
echo "== Запускаем тестовую топологию =="
netlab up &>/dev/null

# получаем список p2p-интерфейсов на R0
iface_names=$(netlab inspect --node r0 interfaces --format json | jq -r '.[] | select(.type == "p2p") | .ifname')

# ждем когда на R0 появятся марщрут через все линки
echo "=== Проверка маршрутов на R0 ==="
while true; do
    current_count=$(netlab exec r0 vtysh -c 'show ip route 10.0.42.0/24' 2>/dev/null | grep 'via eth' | wc -l)      
    if [ $current_count -eq $links_count ]; then
        echo "✓ Успешно! Получено $current_count маршрутов."
        break
    fi
    sleep 1
done

echo "== Начинаем тест А (LPS) =="

# выполняем тесты
for test_num in $(seq 1 $links_count); do

    # запускаем capture на интерфейсах
    echo "=== Запускаем capture на интерфейсах R0, тест ${test_num} ==="
    i=1
    for iface_name in $iface_names; do
        netlab capture r0 $iface_name src 10.1.1.${test_num} -w ../tests/captures/lps_test${test_num}_link${i}.pcap &>/dev/null &
        ((i++))
    done


    # запускаем тестовый трафик (link_packet_sender) на H1, H2
    echo "=== Запускаем тестовый трафик на H1, H2 ==="
    netlab exec h1 python3 /root/links_packet_sender.py --dnet 10.0.42.4/30 --sip 10.1.1.${test_num} --sport 4001-4004 --dport 5001-5004 &>/dev/null
    netlab exec h2 python3 /root/links_packet_sender.py --dnet 10.0.42.4/30 --sip 10.1.1.${test_num} --sport 4001-4004 --dport 5001-5004 &>/dev/null

    # завершаем capture процессы
    echo "=== Останавливаем capture на интерфейсах R0 ==="
    kill -SIGTERM $(jobs -p) 2>/dev/null

done

echo "== Начинаем тест Б (RPS) =="
echo "=== Запускаем capture на интерфейсах R0 ==="
i=1
for iface_name in $iface_names; do
    netlab capture r0 $iface_name dst net 10.0.42.0/24 -w ../tests/captures/rps_link${i}.pcap &>/dev/null &
    ((i++))
done

echo "=== Запускаем тестовый трафик на H1 ==="
netlab exec h1 python3 /root/random_packet_sender.py --count 1000 &>/dev/null

# завершаем capture процессы
echo "=== Останавливаем capture на интерфейсах R0 ==="
kill -SIGTERM $(jobs -p) 2>/dev/null

# выключаем тестовую топологию
echo "== Выключаем тестовую топологию =="
netlab down &>/dev/null

# запускаем анализ pcap
echo "== Стартуем анализ =="
cd ..
LINKS_COUNT=$links_count pytest tests/test_ecmp.py --alluredir=./allure-results --clean-alluredir

echo "== Генерация отчета allure =="
allure generate ./allure-results -o ./allure-report --clean
# получение ip адреса сетевого интерфейса
src_ip=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')
allure open --host $src_ip --port 8080 ./allure-report