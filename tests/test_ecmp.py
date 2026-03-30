#!/usr/bin/env python3
import pytest
import allure
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, os
import sys
from pcap_analyze import TestSuite


@allure.epic("ECMP Тестирование")
@allure.feature("Тест А: LPS (Link Per Source)")
class TestLPS:
    """Тесты для проверки LPS (Link Per Source)"""
    
    @allure.story("Проверка уникальности выбора линка")
    @allure.title("В каждом тесте должен быть выбран только один линк")
    @allure.description("""
        Проверяет, что в каждом тесте (вложенном списке) 
        значение 1 встречается ровно один раз.
        Это подтверждает, что трафик с одного source address
        идет только через один интерфейс.
    """)
    def test_single_link_per_test(self, test_suite):
        with allure.step("Анализ результатов LPS тестов"):
            for test_num, test_results in enumerate(test_suite.lps_test_results):
                with allure.step(f"Проверка теста {test_num + 1}"):
                    ones_count = sum(test_results)
                    
                    allure.attach(
                        str(test_results),
                        name=f"Результаты теста {test_num + 1}",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                    assert ones_count == 1, \
                        f"В тесте {test_num + 1} найдено {ones_count} линков с трафиком, ожидалось 1"
                    
                    selected_link = test_results.index(1)
                    allure.attach(
                        f"Выбран линк: {selected_link + 1}",
                        name=f"Линк для теста {test_num + 1}",
                        attachment_type=allure.attachment_type.TEXT
                    )
    
    @allure.story("Проверка распределения")
    @allure.title("Все линки должны быть задействованы в тестах")
    @allure.description("""
        Проверяет, что каждый линк был выбран хотя бы в одном тесте.
        Это важно для проверки равномерности распределения.
    """)
    @pytest.mark.xfail
    def test_all_links_used(self, test_suite):
        with allure.step("Анализ использования линков"):
            links_usage = [sum(col) for col in zip(*test_suite.lps_test_results)]
            
            for link_num, used_count in enumerate(links_usage):
                with allure.step(f"Проверка линка {link_num + 1}"):
                    allure.attach(
                        f"Количество использований: {used_count}",
                        name=f"Использование линка {link_num + 1}",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                    assert used_count > 0, \
                        f"Линк {link_num + 1} не был использован ни в одном тесте"
    
    @allure.story("Визуализация")
    @allure.title("Тепловая карта распределения трафика")
    def test_heatmap_visualization(self, test_suite):
        """Создает тепловую карту для визуализации распределения"""
        with allure.step("Построение тепловой карты LPS результатов"):
            fig, ax = plt.subplots(figsize=(12, 10))
            
            sns.heatmap(
                test_suite.lps_test_results,
                annot=True,
                fmt='d',
                cmap='YlOrRd',
                cbar_kws={'label': 'Traffic Present'},
                ax=ax
            )
            
            ax.set_xlabel('Link Number')
            ax.set_ylabel('Test Number')
            ax.set_title('ECMP Traffic Distribution (LPS Test)')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            
            allure.attach(
                buf.read(),
                name="Тепловая карта LPS",
                attachment_type=allure.attachment_type.PNG
            )
            plt.close()


@allure.epic("ECMP Тестирование")
@allure.feature("Тест Б: RPS (Rate Per Second)")
class TestRPS:
    """Тесты для проверки RPS (Rate Per Second)"""
    
    @allure.story("Проверка равномерности нагрузки")
    @allure.title("Отклонение RPS на каждом линке не должно превышать 10% от среднего")
    @allure.description("""
        Проверяет, что количество пакетов, прошедших через каждый линк,
        равномерно распределено. Отклонение каждого значения от среднего
        не должно превышать 10%.
    """)
    def test_rps_deviation_within_limit(self, test_suite, tolerance_percent=10):
        with allure.step("Расчет статистики RPS"):
            rps_values = test_suite.rps_test_results
            avg_rps = np.mean(rps_values)
            
            allure.attach(
                str(rps_values),
                name="RPS значения",
                attachment_type=allure.attachment_type.TEXT
            )
            
            allure.attach(
                f"Среднее значение: {avg_rps:.2f}",
                name="Среднее арифметическое",
                attachment_type=allure.attachment_type.TEXT
            )
            
            with allure.step("Проверка ненулевых значений"):
                for link_num, rps in enumerate(rps_values):
                    assert rps > 0, f"Линк {link_num + 1} имеет нулевое значение RPS"
            
            with allure.step("Проверка отклонений"):
                deviations = []
                for link_num, rps in enumerate(rps_values):
                    deviation = abs(rps - avg_rps) / avg_rps * 100
                    deviations.append(deviation)
                    
                    allure.attach(
                        f"RPS={rps}, Отклонение={deviation:.2f}%",
                        name=f"Статистика линка {link_num + 1}",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                    assert deviation <= tolerance_percent, \
                        f"Линк {link_num + 1}: отклонение {deviation:.2f}% превышает {tolerance_percent}%"
    
    @allure.story("Визуализация")
    @allure.title("График отклонений RPS по линкам")
    def test_rps_deviation_visualization(self, test_suite, tolerance_percent=10):
        """Создает график отклонений RPS"""
        with allure.step("Построение графика отклонений"):
            rps_values = test_suite.rps_test_results
            avg_rps = np.mean(rps_values)
            deviations = [abs(rps - avg_rps) / avg_rps * 100 for rps in rps_values]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            bars = ax.bar(range(1, len(rps_values) + 1), deviations, color='skyblue')
            ax.axhline(y=tolerance_percent, color='r', linestyle='--', 
                      linewidth=2, label=f'Limit: {tolerance_percent}%')
            
            # Подсветка bars, превышающих лимит
            for bar, dev in zip(bars, deviations):
                if dev > tolerance_percent:
                    bar.set_color('red')
            
            ax.set_xlabel('Link Number')
            ax.set_ylabel('Deviation (%)')
            ax.set_title('RPS Deviation per Link')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            
            allure.attach(
                buf.read(),
                name="График отклонений RPS",
                attachment_type=allure.attachment_type.PNG
            )
            plt.close()
    
    @allure.story("Проверка статистики")
    @allure.title("Коэффициент вариации RPS не должен превышать 15%")
    @allure.description("""
        Дополнительная проверка равномерности распределения
        через коэффициент вариации (CV = std/mean * 100%).
        CV < 15% считается хорошей равномерностью.
    """)
    def test_coefficient_of_variation(self, test_suite, max_cv_percent=15):
        with allure.step("Расчет коэффициента вариации"):
            rps_values = test_suite.rps_test_results
            mean = np.mean(rps_values)
            std = np.std(rps_values)
            cv = (std / mean) * 100
            
            allure.attach(
                f"Среднее: {mean:.2f}\n"
                f"Стандартное отклонение: {std:.2f}\n"
                f"Коэффициент вариации: {cv:.2f}%",
                name="Статистические показатели",
                attachment_type=allure.attachment_type.TEXT
            )
            
            assert cv <= max_cv_percent, \
                f"Коэффициент вариации {cv:.2f}% превышает {max_cv_percent}%"


@allure.epic("ECMP Тестирование")
@allure.feature("Общие проверки")
class TestCommon:
    """Общие проверки для обоих тестов"""
    
    @allure.story("Проверка данных")
    @allure.title("Все результаты тестов имеют корректную размерность")
    def test_correct_dimensions(self, test_suite):
        with allure.step("Проверка LPS результатов"):
            assert len(test_suite.lps_test_results) == test_suite.links, \
                f"Количество тестов {len(test_suite.lps_test_results)} не соответствует количеству линков {test_suite.links}"
            
            for test_num, test_results in enumerate(test_suite.lps_test_results):
                assert len(test_results) == test_suite.links, \
                    f"Тест {test_num + 1}: размерность {len(test_results)} не соответствует количеству линков {test_suite.links}"
        
        with allure.step("Проверка RPS результатов"):
            assert len(test_suite.rps_test_results) == test_suite.links, \
                f"RPS результаты: размерность {len(test_suite.rps_test_results)} не соответствует количеству линков {test_suite.links}"


# Фикстура для создания объекта TestSuite
@pytest.fixture(scope="session")
def test_suite(request):
    """Фикстура для создания объекта TestSuite"""

    links_count = os.environ.get('LINKS_COUNT')
    
    if links_count is None:
        pytest.fail("Не указано количество линков. Установите переменную LINKS_COUNT")

    suite = TestSuite(int(links_count), './tests/captures')
    suite.process_lps_pcaps()
    suite.process_rps_pcaps()
    
    return suite
